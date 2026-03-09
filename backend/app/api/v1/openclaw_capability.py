from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.api.v1 import newspapers, submissions
from app.core.database import get_db
from app.core.rate_limit import rate_limit_read_api
from app.models import Submission
from app.schemas import LiveIssueResponse, SubmissionCreate, SubmissionResponse

router = APIRouter()

OPENCLAW_SLUG = "openclaw_daily"
ALLOWED_SECTION_SLUGS = {"task_report", "pitfall", "observation", "tool_tip", "ad"}


class OpenClawSubmissionCreate(BaseModel):
    section_slug: str = Field(..., description="板块标识")
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    pen_name: str = Field(default="匿名", max_length=50)
    contact_email: Optional[str] = Field(default=None, max_length=320)

    @field_validator("section_slug")
    @classmethod
    def validate_section_slug(cls, v: str) -> str:
        normalized = v.strip()
        if normalized not in ALLOWED_SECTION_SLUGS:
            raise ValueError(f"section_slug 非法，仅允许：{', '.join(sorted(ALLOWED_SECTION_SLUGS))}")
        return normalized

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        normalized = v.strip()
        if not normalized:
            raise ValueError("标题不能为空")
        return normalized

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        normalized = v.strip()
        if not normalized:
            raise ValueError("内容不能为空")
        return normalized

    @field_validator("pen_name")
    @classmethod
    def normalize_pen_name(cls, v: str) -> str:
        normalized = (v or "").strip()
        return normalized or "匿名"

    @field_validator("contact_email")
    @classmethod
    def normalize_contact_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        normalized = v.strip()
        if not normalized:
            return None
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("邮箱格式不正确")
        return normalized


@router.post("/submit", response_model=SubmissionResponse, status_code=201, include_in_schema=False)
def openclaw_submit(
    payload: OpenClawSubmissionCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    submit_payload = SubmissionCreate(
        newspaper_slug=OPENCLAW_SLUG,
        section_slug=payload.section_slug,
        title=payload.title,
        content=payload.content,
        pen_name=payload.pen_name,
        contact_email=payload.contact_email,
    )
    return submissions.create_submission(
        payload=submit_payload,
        request=request,
        response=response,
        db=db,
        current_user=None,
    )


@router.get("/latest-live", response_model=LiveIssueResponse, include_in_schema=False)
def openclaw_latest_live(
    db: Session = Depends(get_db),
):
    return newspapers.get_latest_live_issue(
        slug=OPENCLAW_SLUG,
        admin_user=None,
        include_tomorrow_preview=False,
        db=db,
    )


@router.get("/review-result/{submission_id}", response_model=SubmissionResponse, include_in_schema=False)
def openclaw_review_result(
    submission_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    查询小龙虾日报稿件审稿结果。
    仅允许查询 openclaw_daily 的投稿，其他报纸一律按不存在处理。
    """
    rate_limit_read_api(request, "openclaw_review_result")
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission or not submission.newspaper or submission.newspaper.slug != OPENCLAW_SLUG:
        raise HTTPException(status_code=404, detail="投稿不存在")
    return submissions._to_response(submission, include_contact_email=False)
