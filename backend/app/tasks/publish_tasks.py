"""
发布任务 (Publish Tasks)

职责边界：
  - generate_layout: 06:30 UTC+8，读取 curated_articles → 自动排版 → 存 DailyIssue
  - publish_issue: 07:00 UTC+8，标记 DailyIssue.is_published = True
"""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

from app.core.database import SessionLocal
from app.core.issue_capacity import get_issue_quotas, get_newspaper_publish_capacity
from app.core.timezone import shanghai_now, shanghai_today
from app.models import CuratedArticle, DailyIssue, Newspaper, Section
from app.services.newspaper_config import get_effective_newspaper_config
from app.tasks.celery_app import celery_app
from app.agents.llm_manager import LLMManager

IMPORTANCE_WEIGHT = {"headline": 5, "secondary": 3, "brief": 1}
# 每页最多放多少篇文章（前端可滚动，所以可以适当多放）
MAX_ARTICLES_PER_PAGE = 8


@celery_app.task
def generate_layout():
    """
    排版任务 — 每日 06:30 UTC+8
    输出统一 layout_data：
      pages[].page_num/section_name/template_used/columns[].items[]
    """
    db = SessionLocal()
    try:
        today = shanghai_today()
        newspapers = db.query(Newspaper).all()
        results = []

        for newspaper in newspapers:
            curated = (
                db.query(CuratedArticle)
                .filter(
                    CuratedArticle.newspaper_id == newspaper.id,
                    CuratedArticle.issue_date == today,
                )
                .all()
            )

            ordered_sections = (
                db.query(Section)
                .filter(Section.newspaper_id == newspaper.id)
                .order_by(Section.sort_order.asc(), Section.id.asc())
                .all()
            )
            section_map = {section.id: section.name for section in ordered_sections}
            articles = [_to_layout_article(c, section_map) for c in curated] if curated else []
            section_candidates = [section.name for section in ordered_sections if section.name]
            layout_data = _build_layout(articles, newspaper.slug, section_candidates)
            layout_article_count = _count_layout_articles(layout_data)

            issue_count = db.query(DailyIssue).filter(DailyIssue.newspaper_id == newspaper.id).count()
            editor_message = _generate_editor_message(newspaper.slug)
            existing_issue = (
                db.query(DailyIssue)
                .filter(
                    DailyIssue.newspaper_id == newspaper.id,
                    DailyIssue.issue_date == today,
                )
                .first()
            )

            if existing_issue:
                issue = existing_issue
            else:
                issue = DailyIssue(
                    newspaper_id=newspaper.id,
                    issue_date=today,
                    issue_number=issue_count + 1,
                )
                db.add(issue)

            issue.layout_data = layout_data
            issue.template_used = layout_data.get("template_used", "经典头版")
            issue.article_count = layout_article_count
            issue.editor_message = editor_message
            issue.is_published = False
            issue.published_at = None
            db.commit()

            results.append(
                {
                    "newspaper": newspaper.slug,
                    "issue_number": issue.issue_number,
                    "article_count": layout_article_count,
                    "status": "layout_ready",
                    "template_used": issue.template_used,
                }
            )

        return results
    finally:
        db.close()


@celery_app.task
def publish_issue():
    """发布任务 — 每日 07:00 UTC+8"""
    db = SessionLocal()
    try:
        today = shanghai_today()
        issues = (
            db.query(DailyIssue)
            .filter(
                DailyIssue.issue_date == today,
                DailyIssue.is_published == False,
            )
            .all()
        )

        published = []
        for issue in issues:
            issue.is_published = True
            issue.published_at = shanghai_now()
            published.append(issue.newspaper_id)

        db.commit()
        return {"published_count": len(published), "date": str(today)}
    finally:
        db.close()


def _to_layout_article(curated: CuratedArticle, section_map: Dict[int, str]) -> Dict:
    return {
        "id": curated.id,
        "title": curated.edited_title or "无标题",
        "content": curated.edited_content or "",
        "author": _resolve_curated_author(curated),
        "column": section_map.get(curated.section_id, "综合"),
        "importance": _normalize_importance(curated.importance),
    }


def _resolve_curated_author(curated: CuratedArticle) -> str:
    if curated.submission and curated.submission.pen_name:
        return curated.submission.pen_name
    note = (curated.editor_note or "").strip()
    if not note:
        return "匿名"
    try:
        parsed = json.loads(note)
        if isinstance(parsed, dict):
            invited_author = str(parsed.get("invited_author", "")).strip()
            if invited_author:
                return invited_author
    except Exception:
        pass
    return "匿名"


def _count_layout_articles(layout_data: Dict) -> int:
    total = 0
    for page in layout_data.get("pages", []):
        for col in page.get("columns", []):
            for item in col.get("items", []):
                if item.get("type") == "article":
                    total += 1
    return total


def _normalize_importance(importance: str) -> str:
    if importance in {"headline", "secondary", "brief"}:
        return importance
    return "brief"


def _ensure_min_articles(articles: List[Dict], newspaper_slug: str, section_candidates: List[str]) -> List[Dict]:
    """
    文章不足时用 LLM 自动补稿，并做标题去重。
    """
    deduped: List[Dict] = []
    seen_titles = set()
    for article in articles:
        title_key = (article.get("title") or "").strip().lower()
        if not title_key or title_key in seen_titles:
            continue
        seen_titles.add(title_key)
        deduped.append(article)

    target = get_newspaper_publish_capacity(newspaper_slug)
    if len(deduped) >= target:
        return deduped

    need = target - len(deduped)
    llm_generated = _generate_articles_with_llm(
        newspaper_slug=newspaper_slug,
        section_candidates=section_candidates,
        existing_titles=[a.get("title", "") for a in deduped],
        need_count=need,
    )

    for idx, item in enumerate(llm_generated):
        title_key = (item.get("title") or "").strip().lower()
        if not title_key or title_key in seen_titles:
            continue
        seen_titles.add(title_key)
        deduped.append(
            {
                "id": f"ai-fill-{newspaper_slug}-{idx + 1}",
                "title": item.get("title", "自动补稿"),
                "content": item.get("content", "（自动补稿）"),
                "author": item.get("author", "AI编辑部"),
                "column": item.get("column", section_candidates[0] if section_candidates else "综合"),
                "importance": _normalize_importance(item.get("importance", "brief")),
            }
        )
        if len(deduped) >= target:
            break

    if len(deduped) < target:
        fallback = _fallback_generated_articles(newspaper_slug, section_candidates, target - len(deduped))
        for idx, item in enumerate(fallback):
            deduped.append(
                {
                    "id": f"ai-fallback-{newspaper_slug}-{idx + 1}",
                    "title": item["title"],
                    "content": item["content"],
                    "author": item["author"],
                    "column": item["column"],
                    "importance": item["importance"],
                }
            )

    return deduped


def _generate_articles_with_llm(
    newspaper_slug: str,
    section_candidates: List[str],
    existing_titles: List[str],
    need_count: int,
    allowed_importances: List[str] | None = None,
    page_hint: str = "",
) -> List[Dict]:
    prompt = _build_fill_prompt(
        newspaper_slug=newspaper_slug,
        section_candidates=section_candidates,
        existing_titles=existing_titles,
        need_count=need_count,
        allowed_importances=allowed_importances or ["secondary", "brief"],
        page_hint=page_hint,
    )
    try:
        llm = LLMManager()
        response = llm.call(
            model_key="gemini-3.1-flash-lite",
            system_prompt="你是硅基印务局的值班编辑，只输出 JSON。",
            user_message=prompt,
            temperature=0.9,
        )
        return _parse_generated_json(response)
    except Exception:
        return []


def _build_fill_prompt(
    newspaper_slug: str,
    section_candidates: List[str],
    existing_titles: List[str],
    need_count: int,
    allowed_importances: List[str],
    page_hint: str,
) -> str:
    db = SessionLocal()
    try:
        style_hint = get_effective_newspaper_config(db, newspaper_slug=newspaper_slug).get("invite_config", {}).get("style_hint")
    finally:
        db.close()
    style_hint = style_hint or "有叙事张力，先抓人再落地，别写成公文"
    sections = "、".join(section_candidates) if section_candidates else "综合"
    importances = " / ".join(allowed_importances)
    used_titles = "\n".join(f"- {t}" for t in existing_titles[:30]) or "- （暂无）"

    return f"""
请你为报纸 {newspaper_slug} 的「{page_hint or "版面"}」生成 {need_count} 篇“补版稿件”。

要求：
1) 风格：{style_hint}
2) 主题尽量多样，不要重复，避免与现有标题撞车
3) 每篇 content 长度 180~380 字
4) importance 只允许: {importances}
5) column 必须从这些板块中选：{sections}
6) author 给一个像真人的笔名，不要出现 AI、模型、机器人字样

已有标题（禁止重复）：
{used_titles}

严格输出 JSON（不要 markdown）：
{{
  "articles": [
    {{
      "title": "标题",
      "content": "正文",
      "author": "笔名",
      "column": "板块名",
      "importance": "从允许值里选"
    }}
  ]
}}
""".strip()


def _parse_generated_json(response: str) -> List[Dict]:
    raw = response.strip()
    if "```json" in raw:
        raw = raw.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in raw:
        raw = raw.split("```", 1)[1].split("```", 1)[0].strip()

    data = json.loads(raw)
    articles = data.get("articles", [])
    if not isinstance(articles, list):
        return []
    cleaned = []
    for a in articles:
        if not isinstance(a, dict):
            continue
        title = str(a.get("title", "")).strip()
        content = str(a.get("content", "")).strip()
        if not title or not content:
            continue
        cleaned.append(
            {
                "title": title,
                "content": content,
                "author": str(a.get("author", "值班编辑")).strip() or "值班编辑",
                "column": str(a.get("column", "综合")).strip() or "综合",
                "importance": str(a.get("importance", "brief")).strip() or "brief",
            }
        )
    return cleaned


def _fallback_generated_articles(
    newspaper_slug: str,
    section_candidates: List[str],
    count: int,
    forced_importance: str = "brief",
    page_hint: str = "",
) -> List[Dict]:
    section = section_candidates[0] if section_candidates else "综合"
    db = SessionLocal()
    try:
        config = get_effective_newspaper_config(db, newspaper_slug=newspaper_slug)
    finally:
        db.close()
    title_pool = config.get("invite_config", {}).get("fallback_title_pool") or ["头条没响，暗流先上版"]
    paragraph_pool = config.get("invite_config", {}).get("fallback_paragraph_pool") or ["所有叙事都在争夺同一件事：谁有资格定义现场。"]
    base = {
        "title": str(title_pool[0]),
        "content": " ".join(str(item) for item in paragraph_pool[:3]),
        "author": "值班编辑",
        "column": section,
        "importance": forced_importance,
    }
    result = []
    for idx in range(count):
        suffix = f"（{page_hint}补{idx + 1}）" if page_hint else f"（补{idx + 1}）"
        result.append({**base, "title": f"{base['title']}{suffix}"})
    return result


def _build_layout(articles: List[Dict], newspaper_slug: str, section_candidates: List[str]) -> Dict:
    """
    版本配额制：
      - 每个版本有固定 importance 配额
      - 配额不足时，按版本语境调用 LLM 补齐
      - 仍保留 overflow 页（超出配额的真实稿件）
    """
    quota_pages = get_issue_quotas(newspaper_slug)
    section_names = (
        [name for name in section_candidates if name]
        or [str(page.get("template", "")).strip() for page in quota_pages if str(page.get("template", "")).strip()]
        or ["综合"]
    )

    # 标题去重，避免重复稿挤占配额
    deduped: List[Dict] = []
    seen_titles = set()
    for article in articles:
        tkey = (article.get("title") or "").strip().lower()
        if not tkey or tkey in seen_titles:
            continue
        seen_titles.add(tkey)
        deduped.append(article)

    ranked = sorted(
        deduped,
        key=lambda a: (IMPORTANCE_WEIGHT.get(a["importance"], 1), len(a["content"])),
        reverse=True,
    )
    pool = {
        "headline": [a for a in ranked if a["importance"] == "headline"],
        "secondary": [a for a in ranked if a["importance"] == "secondary"],
        "brief": [a for a in ranked if a["importance"] == "brief"],
    }

    # 先做配额分配计划：真实稿能填的先填，缺口记录为并发补稿任务
    page_plans: List[Dict] = []
    generation_jobs: List[Dict] = []
    global_title_snapshot = [a.get("title", "") for a in deduped]

    for idx, page_cfg in enumerate(quota_pages):
        template = page_cfg["template"]
        quota = page_cfg["quota"]
        plan = {
            "idx": idx,
            "template": template,
            "quota": quota,
            "base_articles": [],
            "needs": {},  # {importance: need_count}
        }

        for imp in ("headline", "secondary", "brief"):
            need = int(quota.get(imp, 0))
            while need > 0 and pool[imp]:
                plan["base_articles"].append(pool[imp].pop(0))
                need -= 1
            if need > 0:
                plan["needs"][imp] = need
                generation_jobs.append(
                    {
                        "page_idx": idx,
                        "template": template,
                        "importance": imp,
                        "need_count": need,
                        "existing_titles": global_title_snapshot,
                    }
                )

        page_plans.append(plan)

    # 并发执行所有 LLM 补稿任务
    generated_bucket: Dict[tuple, List[Dict]] = {}
    if generation_jobs:
        max_workers = min(8, len(generation_jobs))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {
                executor.submit(
                    _generate_articles_with_llm,
                    newspaper_slug,
                    section_candidates,
                    job["existing_titles"],
                    job["need_count"],
                    [job["importance"]],
                    job["template"],
                ): job
                for job in generation_jobs
            }
            for future in as_completed(future_map):
                job = future_map[future]
                key = (job["page_idx"], job["importance"])
                try:
                    generated_bucket[key] = future.result() or []
                except Exception:
                    generated_bucket[key] = []

    pages: List[Dict] = []

    # 按页面计划回填补稿（并发结果）+ fallback
    for plan in page_plans:
        idx = plan["idx"]
        template = plan["template"]
        page_articles: List[Dict] = list(plan["base_articles"])

        for imp in ("headline", "secondary", "brief"):
            need = int(plan["needs"].get(imp, 0))
            if need <= 0:
                continue

            generated = generated_bucket.get((idx, imp), [])
            filled = 0

            for g_idx, item in enumerate(generated):
                tkey = (item.get("title") or "").strip().lower()
                if not tkey or tkey in seen_titles:
                    continue
                seen_titles.add(tkey)
                generated_article = {
                    "id": f"ai-fill-{newspaper_slug}-{template}-{idx + 1}-{imp}-{g_idx + 1}",
                    "title": item.get("title", "自动补稿"),
                    "content": item.get("content", "（自动补稿）"),
                    "author": item.get("author", "值班编辑"),
                    "column": item.get("column", section_candidates[0] if section_candidates else "综合"),
                    "importance": _normalize_importance(item.get("importance", imp)),
                }
                page_articles.append(generated_article)
                deduped.append(generated_article)
                filled += 1
                if filled >= need:
                    break

            if filled < need:
                fallback = _fallback_generated_articles(
                    newspaper_slug=newspaper_slug,
                    section_candidates=section_candidates,
                    count=need - filled,
                    forced_importance=imp,
                    page_hint=template,
                )
                for f_idx, item in enumerate(fallback):
                    generated_article = {
                        "id": f"ai-fallback-{newspaper_slug}-{template}-{idx + 1}-{imp}-{f_idx + 1}",
                        "title": item["title"],
                        "content": item["content"],
                        "author": item["author"],
                        "column": item["column"],
                        "importance": item["importance"],
                    }
                    page_articles.append(generated_article)
                    deduped.append(generated_article)

        if page_articles:
            sname = section_names[idx] if idx < len(section_names) else section_names[-1]
            pages.append(
                {
                    "page_num": len(pages) + 1,
                    "section_name": sname,
                    "template_used": template,
                    "columns": _build_scrollable_columns(page_articles, template, newspaper_slug),
                }
            )

    # 剩余真实稿件按 overflow 页继续排
    leftovers = pool["headline"] + pool["secondary"] + pool["brief"]
    leftovers = sorted(
        leftovers,
        key=lambda a: (IMPORTANCE_WEIGHT.get(a["importance"], 1), len(a["content"])),
        reverse=True,
    )
    for i in range(0, len(leftovers), MAX_ARTICLES_PER_PAGE):
        batch = leftovers[i:i + MAX_ARTICLES_PER_PAGE]
        sname = section_names[len(pages)] if len(pages) < len(section_names) else section_names[-1]
        pages.append(
            {
                "page_num": len(pages) + 1,
                "section_name": sname,
                "template_used": "增刊",
                "columns": _build_scrollable_columns(batch, "增刊", newspaper_slug),
            }
        )

    if not pages:
        pages.append(
            {
                "page_num": 1,
                "section_name": section_names[0],
                "template_used": "空",
                "columns": [],
            }
        )

    return {"pages": pages, "template_used": pages[0]["template_used"]}


def _build_scrollable_columns(articles: List[Dict], template: str, newspaper_slug: str) -> List[Dict]:
    """
    三栏布局，完整保留正文，前端负责滚动。
    头版：3/2/1 宽度分配；其余：2/2/2
    """
    fillers = _filler_pool(newspaper_slug)

    if template == "经典头版":
        widths = [3, 2, 1]
    else:
        widths = [2, 2, 2]

    cols: List[List[Dict]] = [[], [], []]

    # 头条优先放最宽列
    queue = list(articles)
    headline = _pop_first(queue, {"headline"})
    if headline:
        cols[0].append(_make_item(headline))
        if cols[0]:
            pass  # 第一条不加分隔线

    # 其余按列轮转分配
    col_cursor = 0 if not headline else 1  # 有头条则第一列先放一条
    for art in queue:
        target = col_cursor % 3
        if cols[target]:
            cols[target].append({"type": "divider"})
        cols[target].append(_make_item(art))
        col_cursor += 1

    # 空列补 filler
    for i, col in enumerate(cols):
        if not col and fillers:
            col.append(fillers.pop(0))

    return [{"width": widths[i], "items": cols[i]} for i in range(3)]


def _make_item(article: Dict) -> Dict:
    return {
        "type": "article",
        "id": article["id"],
        "title": article["title"],
        "content": article["content"],   # 完整正文，不截断
        "author": article["author"],
        "column": article["column"],
        "importance": article["importance"],
    }


def _pop_first(queue: List[Dict], importance_set: set):
    for idx, article in enumerate(queue):
        if article["importance"] in importance_set:
            return queue.pop(idx)
    return None


def _append_with_divider(container: List[Dict], item: Dict):
    if not item:
        return
    if container:
        container.append({"type": "divider"})
    container.append(item)


def _fill_with_filler(container: List[Dict], fillers: List[Dict], target_count: int):
    while len(container) < target_count and fillers:
        _append_with_divider(container, fillers.pop(0))


def _filler_pool(newspaper_slug: str) -> List[Dict]:
    db = SessionLocal()
    try:
        config = get_effective_newspaper_config(db, newspaper_slug=newspaper_slug)
    finally:
        db.close()
    fillers = config.get("publish_config", {}).get("filler_pool") or []
    if isinstance(fillers, list) and fillers:
        return fillers
    return [
        {"type": "quote", "text": "内容在流动，版面是容器。"},
        {"type": "box", "title": "公告", "content": "本页由自动排版系统生成。"},
        {"type": "ad", "style": "classified"},
    ]


def _generate_editor_message(newspaper_slug: str) -> str:
    db = SessionLocal()
    try:
        config = get_effective_newspaper_config(db, newspaper_slug=newspaper_slug)
    finally:
        db.close()
    return config.get("publish_config", {}).get("editor_message") or "本期由自动排版系统生成。"
