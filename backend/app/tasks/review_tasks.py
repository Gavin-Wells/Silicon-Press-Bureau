"""
审稿任务 (Review Tasks)

职责边界：
  - 对单篇投稿进行多维度评分
  - 生成审稿反馈
  - 更新投稿状态为 approved / rejected
  - 如果退稿，触发退稿信生成

不做的事：
  - 编辑润色（由 curation_tasks 处理）
  - 排版（由 publish_tasks 处理）
"""

from app.tasks.celery_app import celery_app
from app.tasks.mail_tasks import send_email_task
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.timezone import shanghai_now
from app.models import Submission, Newspaper, Section, Review, RejectionLetter
from app.services.content_safety import check_submission_content_safety
from app.services.newspaper_config import get_effective_newspaper_config
from app.agents.llm_manager import LLMManager
from app.agents.reviewer import ReviewerAgent, RejectorAgent
from app.services.mail.poster import build_acceptance_poster_png
import base64
import json
import logging

logger = logging.getLogger(__name__)

EDITOR_PEN_NAMES = [
    "夜班校对",
    "铁面审校",
    "纸边观察员",
    "凌晨改稿人",
    "版心巡检",
    "标题雕刻师",
    "语气调音师",
    "错别字猎手",
]

def _get_notification_email(submission: Submission) -> str | None:
    """优先使用投稿时填写邮箱，兼容已有 user.email。"""
    if submission.contact_email:
        return submission.contact_email
    if submission.user and submission.user.email:
        return submission.user.email
    return None


def _apply_newspaper_scoring_profile(
    profile: dict | None,
    raw_total: int,
    dimension_scores: dict | None,
) -> int:
    """
    在模型原始分数之上，按报纸风格做二次修正，确保“同文不同报”评分有差异。
    """
    if not profile:
        return max(0, min(100, int(raw_total)))

    adjusted = float(raw_total) + float(profile.get("base_bias", 0))
    dims = dimension_scores or {}
    for dim_name, factor in profile.get("focus_dims", {}).items():
        if dim_name not in dims:
            continue
        # 以 60 为中位，超过加分，低于减分
        adjusted += (float(dims[dim_name]) - 60.0) * float(factor)

    return max(0, min(100, round(adjusted)))


def _resolve_review_editor_keys() -> tuple[list[str], LLMManager]:
    llm = LLMManager(settings.LLM_CONFIG_PATH)
    available = llm.list_model_keys()
    configured = [item.strip() for item in settings.REVIEW_EDITOR_KEYS.split(",") if item.strip()]

    if configured:
        valid = [item for item in configured if item in available]
        if valid:
            return valid, llm

    if not available:
        raise ValueError("llm.json 中未配置任何可用模型")
    return available, llm


def _aggregate_dimension_scores(
    model_results: list[dict],
    scoring_dims: list[dict],
) -> dict:
    dimension_names = [d["name"] for d in scoring_dims] if scoring_dims else []
    if not dimension_names:
        return {}

    aggregated = {}
    for name in dimension_names:
        values = []
        for item in model_results:
            dims = item.get("dimension_scores") or {}
            if name in dims:
                try:
                    values.append(float(dims[name]))
                except Exception:
                    continue
        if values:
            aggregated[name] = round(sum(values) / len(values))
    return aggregated


def _build_merged_feedback(
    model_results: list[dict],
    final_score: int,
    newspaper_name: str,
) -> str:
    blocks = []
    for item in model_results:
        # 不暴露底层模型名：将模型 key 稳定映射为编辑昵称
        alias_idx = abs(hash(item["model_key"])) % len(EDITOR_PEN_NAMES)
        editor_alias = EDITOR_PEN_NAMES[alias_idx]
        blocks.append(
            f"[编辑：{editor_alias}] 原始分 {item['raw_score']}，风格修正后 {item['adjusted_score']}\n{item.get('feedback', '')}".strip()
        )
    merged = "\n\n---\n\n".join(blocks)
    note = f"[系统注记] 多编辑聚合得分（平均）={final_score}，已应用《{newspaper_name}》风格系数。"
    return f"{merged}\n\n{note}" if merged else note


def _run_single_model_review(
    model_key: str,
    newspaper_slug: str,
    review_prompt: str,
    scoring_profile: dict | None,
    title: str,
    content: str,
    section_name: str,
    scoring_dims: list[dict],
) -> dict:
    reviewer = ReviewerAgent(newspaper_slug, model_key=model_key, review_prompt=review_prompt)
    result = reviewer.review(
        title=title,
        content=content,
        section_name=section_name,
        scoring_dimensions=scoring_dims,
    )
    adjusted_total = _apply_newspaper_scoring_profile(
        profile=scoring_profile,
        raw_total=result["total_score"],
        dimension_scores=result.get("dimension_scores"),
    )
    return {
        "model_key": model_key,
        "raw_score": result["total_score"],
        "adjusted_score": adjusted_total,
        "dimension_scores": result.get("dimension_scores") or {},
        "feedback": result.get("feedback", ""),
        "raw_response": result.get("raw_response", ""),
    }


def _reject_by_content_policy(
    db,
    submission: Submission,
    newspaper: Newspaper,
    reason: str,
) -> None:
    """命中内容安全策略：直接退稿，不进入 LLM 审稿/退稿信生成链路。"""
    review = Review(
        submission_id=submission.id,
        agent_type=newspaper.slug,
        total_score=0,
        dimension_scores={},
        feedback=f"[内容安全拦截]\n{reason}\n\n请调整选题后重新投稿。",
        raw_response='{"blocked_by":"content_safety"}',
    )
    db.add(review)

    submission.status = "rejected"
    submission.reviewed_at = shanghai_now()

    rejection = RejectionLetter(
        submission_id=submission.id,
        letter_content=(
            "很抱歉，你的稿件未通过内容安全审核。\n"
            "当前系统不接收政治相关敏感话题投稿，请调整选题后再试。"
        ),
        letter_style="policy_block",
        is_featured=False,
    )
    db.add(rejection)
    db.commit()


@celery_app.task(bind=True, max_retries=3)
def review_submission(self, submission_id: int):
    """审稿主任务 — 多维度评分"""
    db = SessionLocal()
    submission = None
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            return {"error": "submission not found"}

        newspaper = db.query(Newspaper).filter(Newspaper.id == submission.newspaper_id).first()
        section = db.query(Section).filter(Section.id == submission.section_id).first()

        safety = check_submission_content_safety(submission.title, submission.content)
        if safety.blocked:
            _reject_by_content_policy(db, submission, newspaper, safety.reason or "命中内容安全策略")
            return {
                "submission_id": submission_id,
                "status": "rejected",
                "reason": safety.reason,
                "blocked_by": "content_safety",
            }

        # 更新状态为审稿中
        submission.status = "reviewing"
        db.commit()

        runtime_config = get_effective_newspaper_config(db, newspaper=newspaper)
        scoring_dims = section.scoring_dimensions or []

        editor_keys, llm = _resolve_review_editor_keys()
        per_model_results = []
        errors = []
        max_workers = max(1, min(settings.REVIEW_LLM_MAX_WORKERS, len(editor_keys)))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {
                executor.submit(
                    _run_single_model_review,
                    model_key,
                    newspaper.slug,
                    runtime_config["review_prompt"],
                    runtime_config.get("scoring_profile"),
                    submission.title,
                    submission.content,
                    section.name,
                    scoring_dims,
                ): model_key
                for model_key in editor_keys
            }
            for future in as_completed(future_map):
                model_key = future_map[future]
                try:
                    per_model_results.append(future.result())
                except Exception as exc:
                    errors.append(f"{model_key}: {exc}")

        per_model_results.sort(key=lambda item: editor_keys.index(item["model_key"]))

        if not per_model_results:
            raise RuntimeError(f"所有编辑评审失败：{' | '.join(errors)}")

        final_score = round(
            sum(item["adjusted_score"] for item in per_model_results) / len(per_model_results)
        )
        aggregated_dims = _aggregate_dimension_scores(per_model_results, scoring_dims)
        merged_feedback = _build_merged_feedback(
            per_model_results,
            final_score,
            newspaper.name,
        )
        raw_response = json.dumps(
            {
                "editor_keys": editor_keys,
                "errors": errors,
                "results": per_model_results,
            },
            ensure_ascii=False,
        )

        # 存储审稿结果
        review = Review(
            submission_id=submission_id,
            agent_type=newspaper.slug,
            total_score=final_score,
            dimension_scores=aggregated_dims,
            feedback=merged_feedback,
            raw_response=raw_response,
        )
        db.add(review)

        # 判定
        if final_score >= newspaper.pass_threshold:
            submission.status = "approved"
        else:
            submission.status = "rejected"
            # 异步生成退稿信
            generate_rejection_letter.delay(submission_id, final_score, merged_feedback)

        submission.reviewed_at = shanghai_now()
        db.commit()

        # 审稿通过后发送过稿通知（可选邮箱）
        notification_email = _get_notification_email(submission)
        if submission.status == "approved" and notification_email:
            attachments = []
            try:
                poster_bytes = build_acceptance_poster_png(
                    newspaper_name=newspaper.name,
                    title=submission.title,
                    content=submission.content,
                    homepage_url=settings.SITE_HOME_URL,
                )
                attachments.append(
                    {
                        "filename": "acceptance-poster.png",
                        "mime_type": "image/png",
                        "content_base64": base64.b64encode(poster_bytes).decode("utf-8"),
                    }
                )
            except Exception:
                attachments = []
                logger.exception("failed_to_generate_acceptance_poster", extra={"submission_id": submission.id})

            send_email_task.delay(
                to_email=notification_email,
                subject=f"过稿通知：{submission.title}",
                body_text=(
                    f"您好，{submission.pen_name}：\n\n"
                    f"恭喜！您的投稿《{submission.title}》已通过审核。\n"
                    "我们会在后续排版流程中安排刊发。\n"
                    "已为你附上一张中稿海报，欢迎分享。\n\n"
                    "感谢投稿，期待您的更多作品。"
                ),
                body_html=(
                    f"<p>您好，{submission.pen_name}：</p>"
                    f"<p>恭喜！您的投稿《{submission.title}》已通过审核。</p>"
                    "<p>我们会在后续排版流程中安排刊发。已为你附上一张中稿海报，欢迎分享。</p>"
                    "<p>感谢投稿，期待您的更多作品。</p>"
                ),
                attachments=attachments,
            )

        return {
            "submission_id": submission_id,
            "status": submission.status,
            "score": final_score,
            "editor_count": len(per_model_results),
        }

    except Exception as exc:
        db.rollback()
        retries = int(getattr(self.request, "retries", 0))
        max_retries = int(getattr(self, "max_retries", 3))
        if retries >= max_retries:
            # 避免永久卡在 reviewing，最终失败后回退到 pending 以便人工/系统重试
            fallback = db.query(Submission).filter(Submission.id == submission_id).first()
            if fallback:
                fallback.status = "pending"
                fallback.reviewed_at = None
                db.commit()
            return {
                "submission_id": submission_id,
                "status": "pending",
                "error": f"review failed after retries: {exc}",
            }
        # 重试（指数退避）
        raise self.retry(exc=exc, countdown=2 ** retries)
    finally:
        db.close()


@celery_app.task
def generate_rejection_letter(submission_id: int, score: int, feedback: str):
    """退稿信生成任务 — 与审稿解耦"""
    db = SessionLocal()
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            return

        newspaper = db.query(Newspaper).filter(Newspaper.id == submission.newspaper_id).first()

        runtime_config = get_effective_newspaper_config(db, newspaper=newspaper)
        rejector = RejectorAgent(newspaper.slug, reject_prompt=runtime_config["reject_prompt"])
        letter = rejector.generate_rejection(submission.title, score, feedback)

        rejection = RejectionLetter(
            submission_id=submission_id,
            letter_content=letter,
            letter_style=runtime_config.get("rejection_letter_style", "standard"),
            is_featured=(score < 30),  # 极低分的退稿信可能很精彩
        )
        db.add(rejection)
        db.commit()

        # 退稿后发送通知（若填写邮箱），不影响主流程
        notification_email = _get_notification_email(submission)
        if notification_email:
            send_email_task.delay(
                to_email=notification_email,
                subject=f"投稿结果通知：{submission.title}",
                body_text=(
                    f"您好，{submission.pen_name}：\n\n"
                    f"您的投稿《{submission.title}》未通过审核。\n"
                    "以下是编辑部的反馈：\n\n"
                    f"{letter}\n\n"
                    "感谢投稿，期待您的下一篇作品。"
                ),
            )
    finally:
        db.close()
