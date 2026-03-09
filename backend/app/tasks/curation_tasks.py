"""
选稿任务 (Curation Tasks)

职责边界：
  - 每日 23:00 UTC+8 运行
  - 收集 approved 投稿并择优
  - 稿件不足时触发“邀稿”进入审稿队列
  - 调用 EditorAgent 编辑润色
  - 分配 importance（headline / secondary / brief）
  - 存入 curated_articles 表
"""

import json
import math
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session

from app.agents.llm_manager import LLMManager
from app.agents.reviewer import EditorAgent
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.issue_capacity import get_newspaper_approved_pool_cap, get_newspaper_publish_capacity
from app.core.timezone import shanghai_now
from app.models import CuratedArticle, Newspaper, Review, Section, Submission
from app.services.newspaper_config import get_effective_newspaper_config
from app.services.news_fetcher import fetch_live_news_briefs
from app.services.submission_pipeline import create_submission_record, enqueue_review
from app.tasks.celery_app import celery_app

INVITED_AUTHOR_POOL = [
    "故障诗人404", "热启动阿凛", "低延迟老周", "云栈小未", "观测员K",
    "缓存失忆者", "街角编译器", "夜航日志员", "反转捕手七号", "雾都校对官",
    "未命名通讯员", "断句维修工", "冷门热搜员", "半拍记者L", "注释里的风",
    "旧闻再编辑", "凌晨三点署名", "纸面潜行者", "早报值班", "真相试运行",
]
PREWARM_INVITE_TOTAL = 100
PREWARM_INVITE_BATCH_SIZE = 10


@celery_app.task
def curate_daily_articles(**kwargs):
    """每日选稿主任务

    逻辑：
    1. 获取两份报纸
    2. 对每份报纸，获取当日 approved 且未被选过的投稿
    3. 执行“归档淘汰”：超龄未入选 approved -> archived
    4. 按“评分 + 时效衰减”排序
    5. 新稿保底：至少 X% 配额给近 Y 小时投稿
    6. 按排名分配 importance（headline / secondary / brief）
    7. 对每篇调用 EditorAgent 润色
    8. 邀稿先入 submissions 并进入审稿队列
    9. 存入 curated_articles

    kwargs:
        target_issue_date: 可选，指定出刊日（date 或 "YYYY-MM-DD"）；不传则默认为明天。
    """
    db = SessionLocal()
    try:
        now = shanghai_now()
        raw = kwargs.get("target_issue_date")
        if raw is not None:
            if isinstance(raw, str):
                issue_date = datetime.strptime(raw, "%Y-%m-%d").date()
            elif isinstance(raw, date):
                issue_date = raw
            elif isinstance(raw, datetime):
                issue_date = raw.date()
            else:
                issue_date = datetime.strptime(str(raw), "%Y-%m-%d").date()
        else:
            issue_date = now.date() + timedelta(days=1)  # 默认排入明天的报纸
        newspapers = db.query(Newspaper).all()

        results = []
        curated_subquery = db.query(CuratedArticle.submission_id).filter(
            CuratedArticle.submission_id.isnot(None)
        )

        fresh_window_hours = max(1, settings.CURATION_FRESH_WINDOW_HOURS)
        fresh_quota_ratio = min(1.0, max(0.0, settings.CURATION_FRESH_QUOTA_RATIO))
        decay_per_day = max(0.0, settings.CURATION_TIME_DECAY_PER_DAY)
        archive_after_days = max(1, settings.CURATION_ARCHIVE_AFTER_DAYS)

        for newspaper in newspapers:
            runtime_config = get_effective_newspaper_config(db, newspaper=newspaper)
            daily_limit = get_newspaper_publish_capacity(newspaper.slug, db=db)
            section_rows = (
                db.query(Section)
                .filter(
                    Section.newspaper_id == newspaper.id,
                    Section.is_user_submittable == True,
                )
                .order_by(Section.sort_order.asc(), Section.id.asc())
                .all()
            )
            if not section_rows:
                section_rows = (
                    db.query(Section)
                    .filter(Section.newspaper_id == newspaper.id)
                    .order_by(Section.sort_order.asc(), Section.id.asc())
                    .all()
                )
            if not section_rows:
                results.append(
                    {
                        "newspaper": newspaper.slug,
                        "curated": 0,
                        "archived": 0,
                        "message": "未配置任何板块，跳过",
                    }
                )
                continue

            section_name_to_id = {s.name: s.id for s in section_rows}
            default_section_id = section_rows[0].id

            # ── 1) 归档超龄稿件（防止老高分永远占坑） ──
            archive_before = now - timedelta(days=archive_after_days)
            stale_rows = (
                db.query(Submission)
                .filter(
                    Submission.newspaper_id == newspaper.id,
                    Submission.status == "approved",
                    Submission.submitted_at < archive_before,
                    ~Submission.id.in_(curated_subquery),
                )
                .all()
            )
            archived_count = 0
            for stale in stale_rows:
                stale.status = "archived"
                archived_count += 1
            if archived_count:
                db.commit()

            # ── 1.5) 审核池有空位时，从候补队列补位进入审稿 ──
            promoted_before_curation = _promote_overflow_to_review(
                db=db,
                newspaper_id=newspaper.id,
                newspaper_slug=newspaper.slug,
                curated_subquery=curated_subquery,
            )

            # ── 2) 获取可选稿件（approved 且未被 curate） ──
            approved_rows = (
                db.query(Submission, Review.total_score.label("review_score"))
                .join(Review, Review.submission_id == Submission.id)
                .filter(
                    Submission.newspaper_id == newspaper.id,
                    Submission.status == "approved",
                    ~Submission.id.in_(curated_subquery),
                )
                .order_by(Review.total_score.desc())
                .all()
            )

            # ── 3) 高分优先 + 时效加权（分数衰减） ──
            fresh_cutoff = now - timedelta(hours=fresh_window_hours)
            ranked_rows = []
            for row in approved_rows:
                submission = row[0]
                score = float(row[1] or 0)
                age_seconds = max(0.0, (now - submission.submitted_at).total_seconds())
                age_days = age_seconds / 86400.0
                effective_score = score - (age_days * decay_per_day)
                is_fresh = submission.submitted_at >= fresh_cutoff
                ranked_rows.append({
                    "submission": submission,
                    "score": score,
                    "effective_score": effective_score,
                    "is_fresh": is_fresh,
                })

            ranked_rows.sort(
                key=lambda item: (item["effective_score"], item["score"], item["submission"].submitted_at),
                reverse=True,
            )

            # ── 4) 新稿保底配额（至少 ratio 给近 fresh_window_hours 新稿） ──
            fresh_quota = math.ceil(daily_limit * fresh_quota_ratio)
            fresh_pool = [item for item in ranked_rows if item["is_fresh"]]
            selected = []
            selected_ids = set()

            for item in fresh_pool[:fresh_quota]:
                selected.append(item)
                selected_ids.add(item["submission"].id)

            for item in ranked_rows:
                if len(selected) >= daily_limit:
                    break
                if item["submission"].id in selected_ids:
                    continue
                selected.append(item)
                selected_ids.add(item["submission"].id)

            # 缺口导向邀稿：考虑已过审可选稿 + 待审积压，避免每轮固定灌稿导致持续膨胀。
            in_flight_count = (
                db.query(Submission.id)
                .filter(
                    Submission.newspaper_id == newspaper.id,
                    Submission.status.in_(["pending", "reviewing", "queued_overflow"]),
                    ~Submission.id.in_(curated_subquery),
                )
                .count()
            )
            invite_needed = max(
                settings.CURATION_MIN_INVITE_PER_ISSUE,
                daily_limit - (len(approved_rows) + in_flight_count),
            )
            invite_needed = max(0, invite_needed)
            invite_context_titles = [
                item["submission"].title for item in ranked_rows[:20]
            ]
            invited_articles = _invite_missing_articles_parallel(
                newspaper_slug=newspaper.slug,
                newspaper_name=newspaper.name,
                need_count=invite_needed,
                section_names=[s.name for s in section_rows],
                context_titles=invite_context_titles,
                issue_date=str(issue_date),
                live_news=(
                    fetch_live_news_briefs(
                        newspaper_slug=newspaper.slug,
                        newspaper_name=newspaper.name,
                        editor_persona=newspaper.editor_persona,
                        section_names=[s.name for s in section_rows],
                        news_config=runtime_config.get("news_config"),
                        max_items=settings.INVITE_NEWS_MAX_ITEMS,
                        timeout_seconds=settings.INVITE_NEWS_TIMEOUT_SECONDS,
                    )
                    if settings.INVITE_NEWS_ENABLED
                    else []
                ),
            )

            fresh_selected = 0
            invited_count = 0
            invited_authors: list[str] = []
            invited_submission_ids: list[int] = []
            selected_payloads = []
            for idx, item in enumerate(selected):
                submission = item["submission"]
                score = item["score"] or 0
                if item["is_fresh"]:
                    fresh_selected += 1
                selected_payloads.append(
                    {
                        "idx": idx,
                        "submission": submission,
                        "importance": _assign_importance(idx=idx, score=score),
                    }
                )

            edited_map = _batch_edit_selected_articles(
                newspaper_slug=newspaper.slug,
                selected_payloads=selected_payloads,
                edit_prompt=runtime_config["edit_prompt"],
            )
            for payload in selected_payloads:
                submission = payload["submission"]
                importance = payload["importance"]
                edited = edited_map.get(submission.id) or {
                    "edited_title": submission.title,
                    "edited_content": submission.content,
                }
                curated = CuratedArticle(
                    submission_id=submission.id,
                    newspaper_id=newspaper.id,
                    section_id=submission.section_id,
                    edited_title=edited.get("edited_title", submission.title),
                    edited_content=edited.get("edited_content", submission.content),
                    importance=importance,
                    editor_note=edited.get("editor_note", ""),
                    issue_date=issue_date,
                )
                db.add(curated)

            for offset, invited in enumerate(invited_articles):
                invited_author = (invited.get("author") or "特邀作者").strip() or "特邀作者"
                invited_section = (invited.get("section") or "").strip()
                invited_section_id = section_name_to_id.get(invited_section, default_section_id)
                invited_title = invited.get("title", f"邀稿补位（{offset + 1}）")
                invited_content = invited.get("content", "（邀稿补位内容）")

                # 邀稿与真人稿统一入口：先落 submissions，并走同一审稿流程。
                invited_submission = create_submission_record(
                    db,
                    user_id=None,
                    newspaper_id=newspaper.id,
                    section_id=invited_section_id,
                    title=invited_title,
                    content=invited_content,
                    pen_name=invited_author,
                    contact_email=None,
                    status="pending",
                )
                invited_submission_ids.append(invited_submission.id)
                invited_count += 1
                invited_authors.append(invited_author)

            db.commit()
            for submission_id in invited_submission_ids:
                enqueue_review(submission_id)

            # 本轮选稿后，approved 池会释放空位；继续补位推进下一批候补稿审稿
            promoted_after_curation = _promote_overflow_to_review(
                db=db,
                newspaper_id=newspaper.id,
                newspaper_slug=newspaper.slug,
                curated_subquery=curated_subquery,
            )
            results.append(
                {
                    "newspaper": newspaper.slug,
                    "curated": len(selected),
                    "invited": invited_count,
                    "total_for_issue": len(selected),
                    "fresh_selected": fresh_selected,
                    "fresh_quota_target": min(fresh_quota, len(fresh_pool)),
                    "archived": archived_count,
                    "promoted_overflow": promoted_before_curation + promoted_after_curation,
                    "issue_date": str(issue_date),
                    "invited_authors": invited_authors,
                }
            )

        return results

    finally:
        db.close()


def _promote_overflow_to_review(
    db: Session,
    newspaper_id: int,
    newspaper_slug: str,
    curated_subquery,
) -> int:
    approved_pool_count = (
        db.query(Submission.id)
        .filter(
            Submission.newspaper_id == newspaper_id,
            Submission.status == "approved",
            ~Submission.id.in_(curated_subquery),
        )
        .count()
    )
    approved_pool_cap = get_newspaper_approved_pool_cap(newspaper_slug, db=db)
    available_slots = max(0, approved_pool_cap - int(approved_pool_count))
    if available_slots <= 0:
        return 0

    overflow_rows = (
        db.query(Submission)
        .filter(
            Submission.newspaper_id == newspaper_id,
            Submission.status == "queued_overflow",
        )
        .order_by(Submission.submitted_at.asc(), Submission.id.asc())
        .limit(available_slots)
        .all()
    )
    if not overflow_rows:
        return 0

    promoted_ids = []
    for row in overflow_rows:
        row.status = "pending"
        row.reviewed_at = None
        promoted_ids.append(row.id)
    db.commit()

    for submission_id in promoted_ids:
        enqueue_review(submission_id)

    return len(promoted_ids)


def _assign_importance(idx: int, score: int) -> str:
    """
    importance 规则（稳定且易解释）：
      - 第 1 篇且分数>=80：headline
      - 前 3 篇且分数>=70：secondary
      - 其余：brief
    """
    if idx == 0 and score >= 80:
        return "headline"
    if idx <= 2 and score >= 70:
        return "secondary"
    return "brief"


def _normalize_importance(value: str) -> str:
    if value in {"headline", "secondary", "brief"}:
        return value
    return "brief"


def _pick_invited_authors(newspaper_slug: str, issue_date: str, count: int) -> list[str]:
    rng = random.Random(f"{newspaper_slug}-{issue_date}")
    shuffled = INVITED_AUTHOR_POOL[:]
    rng.shuffle(shuffled)
    return shuffled[:count]


def _edit_one_submission(newspaper_slug: str, title: str, content: str, edit_prompt: str | None = None) -> dict:
    editor = EditorAgent(newspaper_slug, edit_prompt=edit_prompt)
    try:
        return editor.edit(title, content)
    except Exception:
        return {
            "edited_title": title,
            "edited_content": content,
            "editor_note": "编辑调用失败，回退原文",
        }


def _batch_edit_selected_articles(
    newspaper_slug: str,
    selected_payloads: list[dict],
    edit_prompt: str | None = None,
) -> dict[int, dict]:
    if not selected_payloads:
        return {}
    max_workers = max(1, min(settings.CURATION_LLM_MAX_WORKERS, len(selected_payloads)))
    result_map: dict[int, dict] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(
                _edit_one_submission,
                newspaper_slug,
                payload["submission"].title,
                payload["submission"].content,
                edit_prompt,
            ): payload["submission"].id
            for payload in selected_payloads
        }
        for future in as_completed(future_map):
            sid = future_map[future]
            try:
                result_map[sid] = future.result()
            except Exception:
                # 兜底由上游写库时处理
                continue
    return result_map


def _invite_missing_articles(
    newspaper_slug: str,
    newspaper_name: str,
    need_count: int,
    section_names: list[str],
    context_titles: list[str],
    issue_date: str,
    live_news: list[dict],
) -> list[dict]:
    if need_count <= 0:
        return []

    authors = _pick_invited_authors(newspaper_slug, issue_date, min(need_count, len(INVITED_AUTHOR_POOL)))
    llm_result = _invite_articles_with_llm(
        newspaper_slug=newspaper_slug,
        newspaper_name=newspaper_name,
        need_count=len(authors),
        authors=authors,
        section_names=section_names,
        context_titles=context_titles,
        live_news=live_news,
    )
    if llm_result:
        return llm_result[:need_count]
    return _fallback_invited_articles(
        newspaper_slug=newspaper_slug,
        need_count=len(authors),
        authors=authors,
        section_names=section_names,
        live_news=live_news,
    )[:need_count]


def _invite_missing_articles_parallel(
    newspaper_slug: str,
    newspaper_name: str,
    need_count: int,
    section_names: list[str],
    context_titles: list[str],
    issue_date: str,
    live_news: list[dict],
) -> list[dict]:
    if need_count <= 0:
        return []

    batch_size = max(1, PREWARM_INVITE_BATCH_SIZE)
    job_count = math.ceil(need_count / batch_size)
    max_workers = max(1, min(settings.CURATION_LLM_MAX_WORKERS, job_count))

    all_rows: list[dict] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {}
        for idx in range(job_count):
            this_count = min(batch_size, need_count - (idx * batch_size))
            if this_count <= 0:
                continue
            future = executor.submit(
                _invite_missing_articles,
                newspaper_slug,
                newspaper_name,
                this_count,
                section_names,
                context_titles,
                f"{issue_date}-batch-{idx + 1}",
                live_news,
            )
            future_map[future] = idx

        for future in as_completed(future_map):
            try:
                rows = future.result() or []
                if rows:
                    all_rows.extend(rows)
            except Exception:
                continue

    return all_rows[:need_count]


def _invite_articles_with_llm(
    newspaper_slug: str,
    newspaper_name: str,
    need_count: int,
    authors: list[str],
    section_names: list[str],
    context_titles: list[str],
    live_news: list[dict],
) -> list[dict]:
    llm = LLMManager(settings.LLM_CONFIG_PATH)
    model_key = settings.INVITE_EDITOR_KEY.strip() or "gemini-3.1-flash-lite"
    if model_key not in llm.list_model_keys():
        keys = llm.list_model_keys()
        if not keys:
            return []
        model_key = keys[0]

    section_text = "、".join(section_names) if section_names else "综合"
    title_text = "\n".join(f"- {title}" for title in context_titles[:20]) or "- 暂无真人稿件"
    author_text = "\n".join(f"- {name}" for name in authors)
    live_news_text = _format_live_news_cards(live_news)
    style_hint = _invite_style_hint(newspaper_slug)
    prompt = f"""
你是《{newspaper_name}》夜班编辑。现在进入“邀稿补位”流程，需要为明日版面补齐稿件。

要求：
1) 一共生成 {need_count} 篇稿件，每篇绑定一个不同作者，且作者必须来自给定名单。
2) 稿件必须贴合报纸风格（slug={newspaper_slug}）并与既有选题相关，避免同质化。风格指引：{style_hint}
3) section 只能从这些板块中选择：{section_text}
4) importance 只能是：headline / secondary / brief
5) content 长度 220~420 字，必须分成 3~4 段，不要平铺直叙。
6) 如模型具备联网能力，可参考实时信息；若无法联网，基于通用事实写作，禁止编造“具体时间+具体数字+具体来源”。
7) 为抖音直播可读性优化：第一段前两句要有钩子感；至少出现 1 句可被单独截出来的“金句”（能传播的狠话、扎心句、搞钱/焦虑/反差向）。
8) 标题必须有辨识度，长度 10~22 字，禁止“观察/浅谈/思考/分析”这类普通词结尾。标题与正文必须带「搞钱/焦虑/反差/争议」中的至少一种气质，禁止温吞、官话、泛泛而谈。
9) 严格返回 JSON，不要 markdown。

既有真人稿件标题（用于“相关性”参考）：
{title_text}

实时事实卡片（必须优先参考，禁止凭空编造）：
{live_news_text}

可邀作者名单（每人最多 1 篇）：
{author_text}

输出格式：
{{
  "articles": [
    {{
      "title": "标题",
      "content": "正文",
      "author": "必须来自名单",
      "section": "板块名",
      "importance": "headline|secondary|brief",
      "evidence_ids": ["N1", "N2"]
    }}
  ]
}}
""".strip()
    try:
        raw = llm.call(
            model_key=model_key,
            system_prompt="你是资深报刊编辑，只输出严格 JSON。",
            user_message=prompt,
            temperature=1.0,
        )
        return _parse_invited_articles(
            raw,
            allowed_authors=set(authors),
            allowed_sections=section_names,
            live_news=live_news,
        )
    except Exception:
        return []


def _parse_invited_articles(
    response: str,
    allowed_authors: set[str],
    allowed_sections: list[str],
    live_news: list[dict],
) -> list[dict]:
    raw = response.strip()
    if "```json" in raw:
        raw = raw.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in raw:
        raw = raw.split("```", 1)[1].split("```", 1)[0].strip()

    data = json.loads(raw)
    rows = data.get("articles", [])
    if not isinstance(rows, list):
        return []

    result: list[dict] = []
    used_authors = set()
    section_set = set(allowed_sections)
    default_section = allowed_sections[0] if allowed_sections else "综合"
    evidence_map = {item.get("id"): item for item in live_news if isinstance(item, dict)}
    for row in rows:
        if not isinstance(row, dict):
            continue
        title = str(row.get("title", "")).strip()
        content = str(row.get("content", "")).strip()
        author = str(row.get("author", "")).strip()
        section = str(row.get("section", "")).strip()
        importance = _normalize_importance(str(row.get("importance", "brief")).strip())
        evidence_ids = row.get("evidence_ids", [])
        if not title or not content:
            continue
        if author not in allowed_authors or author in used_authors:
            continue
        if not section or (section_set and section not in section_set):
            section = default_section
        if not isinstance(evidence_ids, list):
            evidence_ids = []
        clean_evidence_ids = []
        evidence = []
        for value in evidence_ids:
            evidence_id = str(value).strip()
            if not evidence_id or evidence_id in clean_evidence_ids:
                continue
            if evidence_id in evidence_map:
                clean_evidence_ids.append(evidence_id)
                evidence.append(evidence_map[evidence_id])
        used_authors.add(author)
        result.append(
            {
                "title": title,
                "content": content,
                "author": author,
                "section": section,
                "importance": importance,
                "evidence_ids": clean_evidence_ids,
                "evidence": evidence,
                "news_mode": "live" if clean_evidence_ids else "none",
            }
        )
    return result


def _fallback_invited_articles(
    newspaper_slug: str,
    need_count: int,
    authors: list[str],
    section_names: list[str],
    live_news: list[dict],
) -> list[dict]:
    section = section_names[0] if section_names else "综合"
    title_pool = _fallback_title_pool(newspaper_slug)
    paragraph_pool = _fallback_paragraph_pool(newspaper_slug)
    evidence_pick = live_news[:2]
    rows: list[dict] = []
    for idx in range(need_count):
        author = authors[idx] if idx < len(authors) else f"特邀作者{idx + 1}"
        title = title_pool[idx % len(title_pool)]
        p1 = paragraph_pool[idx % len(paragraph_pool)]
        p2 = paragraph_pool[(idx + 1) % len(paragraph_pool)]
        p3 = paragraph_pool[(idx + 2) % len(paragraph_pool)]
        if evidence_pick:
            clue = evidence_pick[idx % len(evidence_pick)]
            p3 = (
                f"{p3} 线索注记：{clue.get('title', '')}（{clue.get('source', '未知来源')}）"
                f" {clue.get('url', '')}"
            )
        rows.append(
            {
                "title": title,
                "content": f"{p1}\n\n{p2}\n\n{p3}",
                "author": author,
                "section": section,
                "importance": "brief",
                "evidence_ids": [item.get("id") for item in evidence_pick if item.get("id")],
                "evidence": evidence_pick,
                "news_mode": "live_fallback" if evidence_pick else "fallback",
            }
        )
    return rows


def _format_live_news_cards(live_news: list[dict]) -> str:
    if not live_news:
        return "- 未抓取到实时卡片（请基于可验证常识写作，并避免具体时间线断言）"
    lines = []
    for item in live_news:
        if not isinstance(item, dict):
            continue
        nid = item.get("id", "N?")
        title = item.get("title", "无标题")
        source = item.get("source", "未知来源")
        published_at = item.get("published_at", "")
        url = item.get("url", "")
        lines.append(f"- [{nid}] {title} | {source} | {published_at} | {url}")
    return "\n".join(lines) if lines else "- 未抓取到实时卡片"


def _invite_style_hint(newspaper_slug: str) -> str:
    db = SessionLocal()
    try:
        config = get_effective_newspaper_config(db, newspaper_slug=newspaper_slug)
        return config.get("invite_config", {}).get("style_hint") or "有叙事张力，先抓人再落地，别写成公文"
    finally:
        db.close()


def _fallback_title_pool(newspaper_slug: str) -> list[str]:
    db = SessionLocal()
    try:
        config = get_effective_newspaper_config(db, newspaper_slug=newspaper_slug)
        pool = config.get("invite_config", {}).get("fallback_title_pool") or []
        return [str(item).strip() for item in pool if str(item).strip()] or [
            "头条没响，暗流先上版",
            "今天的噪音终于有了名字",
            "纸面之下还有第二现场",
        ]
    finally:
        db.close()


def _fallback_paragraph_pool(newspaper_slug: str) -> list[str]:
    db = SessionLocal()
    try:
        config = get_effective_newspaper_config(db, newspaper_slug=newspaper_slug)
        pool = config.get("invite_config", {}).get("fallback_paragraph_pool") or []
        return [str(item).strip() for item in pool if str(item).strip()] or [
            "头版不是最大的声音，而是最先被验证的声音。",
            "所有叙事都在争夺同一件事：谁有资格定义现场。",
            "如果没有第二证据，第一情绪就只能算草稿。",
        ]
    finally:
        db.close()
