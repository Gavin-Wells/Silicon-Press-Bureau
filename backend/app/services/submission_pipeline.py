from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Submission


def create_submission_record(
    db: Session,
    *,
    newspaper_id: int,
    section_id: int,
    title: str,
    content: str,
    pen_name: str,
    user_id: int | None = None,
    contact_email: str | None = None,
    status: str = "pending",
    submitted_at: datetime | None = None,
    reviewed_at: datetime | None = None,
) -> Submission:
    submission = Submission(
        user_id=user_id,
        newspaper_id=newspaper_id,
        section_id=section_id,
        title=title,
        content=content,
        pen_name=pen_name,
        contact_email=contact_email,
        char_count=len(content),
        status=status,
        submitted_at=submitted_at,
        reviewed_at=reviewed_at,
    )
    db.add(submission)
    db.flush()
    return submission


def enqueue_review(submission_id: int) -> None:
    # 延迟导入避免循环依赖：submission_pipeline 被 API/任务层复用。
    from app.tasks.review_tasks import review_submission

    review_submission.delay(submission_id)
