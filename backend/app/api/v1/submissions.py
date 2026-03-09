"""
投稿 API — /api/v1/submissions

职责边界：
  - 接收投稿、验证字数/板块
  - 存入数据库
  - 触发异步审稿任务
  - 查询投稿状态

不做的事：
  - 审稿逻辑（由 review_tasks 处理）
  - 编辑润色（由 curation_tasks 处理）
  - 排版发布（由 publish_tasks 处理）
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional

from app.agents.llm_manager import LLMManager
from app.agents.reviewer import ReviewerAgent
from app.core.config import settings
from app.core.database import get_db
from app.core.issue_capacity import get_newspaper_approved_pool_cap
from app.models import Submission, Newspaper, Section, User, CuratedArticle
from app.services.submission_pipeline import create_submission_record, enqueue_review
from app.services.newspaper_config import get_effective_newspaper_config, get_section_config, validate_char_count
from app.schemas import (
    SubmissionCreate,
    SubmissionResponse,
    SubmissionBriefResponse,
    SubmissionCompareRequest,
    SubmissionCompareResponse,
)
from app.services.anti_spam import (
    ensure_anon_id,
    get_client_ip,
    enforce_anonymous_submission_guard,
)
from app.core.auth import get_current_user_optional, get_current_user_required
from app.core.rate_limit import rate_limit_compare, rate_limit_user_submit, rate_limit_read_api

router = APIRouter()

OVERFLOW_QUEUE_MESSAGE = "本期审核席位已满，已进入候补队列，系统会自动补位审核"


def _reached_approved_pool_cap(db: Session, newspaper_id: int, newspaper_slug: str) -> bool:
    curated_subquery = db.query(CuratedArticle.submission_id).filter(
        CuratedArticle.submission_id.isnot(None)
    )
    approved_pool_count = (
        db.query(func.count(Submission.id))
        .filter(
            Submission.newspaper_id == newspaper_id,
            Submission.status == "approved",
            ~Submission.id.in_(curated_subquery),
        )
        .scalar()
        or 0
    )
    return int(approved_pool_count) >= get_newspaper_approved_pool_cap(newspaper_slug, db=db)


@router.post("", response_model=SubmissionResponse, status_code=201)
def create_submission(
    payload: SubmissionCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """创建投稿"""

    # 1. 查找报纸
    newspaper = db.query(Newspaper).filter(
        Newspaper.slug == payload.newspaper_slug
    ).first()
    if not newspaper:
        raise HTTPException(status_code=404, detail=f"报纸 '{payload.newspaper_slug}' 不存在")

    # 2. 查找板块
    section = db.query(Section).filter(
        Section.newspaper_id == newspaper.id,
        Section.slug == payload.section_slug
    ).first()
    if not section:
        raise HTTPException(status_code=404, detail=f"板块 '{payload.section_slug}' 不存在")

    if not section.is_user_submittable:
        raise HTTPException(status_code=403, detail=f"板块 '{section.name}' 不接受用户投稿")

    # 3. 验证字数
    is_valid, error_msg = validate_char_count(db, payload.newspaper_slug, payload.section_slug, payload.content)
    if not is_valid:
        raise HTTPException(status_code=422, detail=error_msg)

    # 4. 用户校验（可选登录）：user_id 仅从 JWT 获取，不信任请求体
    user_id = current_user.id if current_user else None
    if user_id is not None:
        rate_limit_user_submit(user_id)
    if user_id is None:
        # 匿名投稿防刷：同匿名 ID / 同 IP 限流 + 内容去重
        anon_id = ensure_anon_id(request, response)
        client_ip = get_client_ip(request)
        enforce_anonymous_submission_guard(
            anon_id=anon_id,
            client_ip=client_ip,
            title=payload.title,
            content=payload.content,
        )

    # 5. 创建投稿记录（若 approved 池已满，则进入候补队列，不直接淘汰）
    initial_status = "queued_overflow" if _reached_approved_pool_cap(db, newspaper.id, newspaper.slug) else "pending"
    submission = create_submission_record(
        db,
        user_id=user_id,
        newspaper_id=newspaper.id,
        section_id=section.id,
        title=payload.title,
        content=payload.content,
        pen_name=payload.pen_name,
        contact_email=payload.contact_email,
        status=initial_status,
    )
    db.commit()
    db.refresh(submission)

    # 6. 触发异步审稿（候补队列暂不入队，等待系统补位）
    if submission.status == "pending":
        enqueue_review(submission.id)

    # 7. 组装响应
    return _to_response(submission, include_contact_email=True)


@router.post("/compare", response_model=SubmissionCompareResponse)
def compare_submission_with_editors(
    payload: SubmissionCompareRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """同一篇稿件交给多位编辑独立评审，返回多份结果对比。"""
    rate_limit_compare(request, current_user.id if current_user else None)

    newspaper = db.query(Newspaper).filter(
        Newspaper.slug == payload.newspaper_slug
    ).first()
    if not newspaper:
        raise HTTPException(status_code=404, detail=f"报纸 '{payload.newspaper_slug}' 不存在")

    section = db.query(Section).filter(
        Section.newspaper_id == newspaper.id,
        Section.slug == payload.section_slug
    ).first()
    if not section:
        raise HTTPException(status_code=404, detail=f"板块 '{payload.section_slug}' 不存在")

    if not section.is_user_submittable:
        raise HTTPException(status_code=403, detail=f"板块 '{section.name}' 不接受用户投稿")

    is_valid, error_msg = validate_char_count(db, payload.newspaper_slug, payload.section_slug, payload.content)
    if not is_valid:
        raise HTTPException(status_code=422, detail=error_msg)

    llm = LLMManager(settings.LLM_CONFIG_PATH)
    editor_keys = _resolve_editor_keys(llm, payload.editor_keys)
    section_def = get_section_config(db, payload.newspaper_slug, payload.section_slug)
    scoring_dims = section_def["scoring_dimensions"] if section_def else []
    runtime_config = get_effective_newspaper_config(db, newspaper=newspaper)

    reviews = []
    max_workers = min(6, len(editor_keys))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(
                _review_with_editor,
                model_key,
                llm.get_display_name(model_key),
                newspaper.slug,
                newspaper.pass_threshold,
                payload.title,
                payload.content,
                section.name,
                scoring_dims,
                runtime_config["review_prompt"],
            ): model_key
            for model_key in editor_keys
        }
        for future in as_completed(future_map):
            reviews.append(future.result())

    reviews.sort(key=lambda item: editor_keys.index(item["editor_key"]))

    return {
        "newspaper_slug": newspaper.slug,
        "newspaper_name": newspaper.name,
        "section_slug": section.slug,
        "section_name": section.name,
        "editor_count": len(reviews),
        "reviews": reviews,
    }


@router.get("/me", response_model=List[SubmissionBriefResponse])
def get_my_submissions(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """查询当前登录用户的投稿列表（需鉴权）"""
    rate_limit_read_api(request, "submissions_me")
    submissions = (
        db.query(Submission)
        .filter(Submission.user_id == current_user.id)
        .order_by(Submission.submitted_at.desc())
        .all()
    )
    return [_to_brief(s) for s in submissions]


@router.get("/by-pen-name/{pen_name}", response_model=List[SubmissionBriefResponse])
def get_submissions_by_pen_name(pen_name: str, request: Request, db: Session = Depends(get_db)):
    """按笔名查询投稿列表"""
    rate_limit_read_api(request, "submissions_by_pen_name")
    submissions = db.query(Submission).filter(
        Submission.pen_name == pen_name
    ).order_by(Submission.submitted_at.desc()).all()

    return [_to_brief(s) for s in submissions]


@router.get("/{submission_id}", response_model=SubmissionResponse)
def get_submission(
    submission_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """查询单篇投稿详情（含审稿结果）"""
    rate_limit_read_api(request, "submission_detail")
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="投稿不存在")
    include_contact_email = bool(
        current_user and submission.user_id and current_user.id == submission.user_id
    )
    return _to_response(submission, include_contact_email=include_contact_email)


@router.get("/newspaper/{newspaper_slug}", response_model=List[SubmissionBriefResponse])
def get_submissions_by_newspaper(
    newspaper_slug: str,
    request: Request,
    status: str = None,
    db: Session = Depends(get_db)
):
    """按报纸查询投稿列表（可按状态过滤）"""
    rate_limit_read_api(request, "submissions_by_newspaper")
    newspaper = db.query(Newspaper).filter(Newspaper.slug == newspaper_slug).first()
    if not newspaper:
        raise HTTPException(status_code=404, detail="报纸不存在")

    query = db.query(Submission).filter(Submission.newspaper_id == newspaper.id)
    if status:
        query = query.filter(Submission.status == status)

    submissions = query.order_by(Submission.submitted_at.desc()).limit(50).all()
    return [_to_brief(s) for s in submissions]


# ── 内部辅助 ──

def _to_response(s: Submission, include_contact_email: bool = False) -> dict:
    """将 ORM 对象转为 API 响应"""
    result = {
        "id": s.id,
        "title": s.title,
        "content": s.content,
        "pen_name": s.pen_name,
        "contact_email": s.contact_email if include_contact_email else None,
        "char_count": s.char_count,
        "status": s.status,
        "newspaper_slug": s.newspaper.slug if s.newspaper else None,
        "section_name": s.section.name if s.section else None,
        "newspaper_name": s.newspaper.name if s.newspaper else None,
        "submitted_at": s.submitted_at,
        "reviewed_at": s.reviewed_at,
        "review": None,
    }
    if s.review:
        result["review"] = {
            "total_score": s.review.total_score,
            "dimension_scores": s.review.dimension_scores,
            "feedback": s.review.feedback,
            "created_at": s.review.created_at,
        }
    return result


def _resolve_editor_keys(llm: LLMManager, requested_keys: List[str] | None) -> List[str]:
    available = llm.list_model_keys()

    if requested_keys:
        invalid = [key for key in requested_keys if key not in available]
        if invalid:
            raise HTTPException(status_code=422, detail=f"以下编辑不存在：{', '.join(invalid)}")
        return requested_keys

    configured = [item.strip() for item in settings.REVIEW_EDITOR_KEYS.split(",") if item.strip()]
    if configured:
        invalid = [key for key in configured if key not in available]
        if invalid:
            raise HTTPException(status_code=500, detail=f"REVIEW_EDITOR_KEYS 配置无效：{', '.join(invalid)}")
        return configured

    if not available:
        raise HTTPException(status_code=500, detail="当前没有可用的编辑模型配置")
    return available


def _review_with_editor(
    model_key: str,
    editor_name: str,
    newspaper_slug: str,
    threshold: int,
    title: str,
    content: str,
    section_name: str,
    scoring_dims: List[dict],
    review_prompt: str,
) -> dict:
    try:
        reviewer = ReviewerAgent(newspaper_slug, model_key=model_key, review_prompt=review_prompt)
        result = reviewer.review(
            title=title,
            content=content,
            section_name=section_name,
            scoring_dimensions=scoring_dims,
        )
        score = result.get("total_score")
        passed = score is not None and score >= threshold
        return {
            "editor_key": model_key,
            "editor_name": editor_name,
            "score": score,
            "passed": passed,
            "verdict": "通过" if passed else "退回",
            "threshold": threshold,
            "dimension_scores": result.get("dimension_scores"),
            "feedback": result.get("feedback"),
            "error": None,
        }
    except Exception as exc:
        return {
            "editor_key": model_key,
            "editor_name": editor_name,
            "score": None,
            "passed": False,
            "verdict": "评审失败",
            "threshold": threshold,
            "dimension_scores": None,
            "feedback": None,
            "error": str(exc),
        }


def _to_brief(s: Submission) -> dict:
    rejection_reason = None
    if s.status == "rejected":
        # 优先展示退稿信；若退稿信未生成，回退到审稿评语
        if s.rejection and s.rejection.letter_content:
            rejection_reason = s.rejection.letter_content
        elif s.review and s.review.feedback:
            rejection_reason = s.review.feedback
    elif s.status == "queued_overflow":
        rejection_reason = OVERFLOW_QUEUE_MESSAGE

    return {
        "id": s.id,
        "title": s.title,
        "content": s.content,
        "pen_name": s.pen_name,
        "char_count": s.char_count,
        "status": s.status,
        "newspaper_slug": s.newspaper.slug if s.newspaper else None,
        "score": s.review.total_score if s.review else None,
        "section_name": s.section.name if s.section else None,
        "newspaper_name": s.newspaper.name if s.newspaper else None,
        "rejection_reason": rejection_reason,
        "submitted_at": s.submitted_at,
    }
