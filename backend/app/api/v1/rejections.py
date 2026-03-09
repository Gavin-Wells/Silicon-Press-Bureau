from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import RejectionLetter, Submission
from typing import List

router = APIRouter()

@router.get("/featured")
def get_featured_rejections(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
    db: Session = Depends(get_db),
):
    base_query = db.query(RejectionLetter, Submission).join(
        Submission, RejectionLetter.submission_id == Submission.id
    )
    total = (
        db.query(func.count(RejectionLetter.id))
        .join(Submission, RejectionLetter.submission_id == Submission.id)
        .scalar()
        or 0
    )
    offset = (page - 1) * page_size
    rejections = (
        base_query
        .order_by(RejectionLetter.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    items = [
        {
            "id": r.RejectionLetter.id,
            "letter_content": r.RejectionLetter.letter_content,
            "submission_title": r.Submission.title,
            "newspaper_slug": r.Submission.newspaper.slug if r.Submission.newspaper else None,
            "newspaper_name": r.Submission.newspaper.name if r.Submission.newspaper else "未知报纸",
            "created_at": r.RejectionLetter.created_at
        }
        for r in rejections
    ]

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": int(total),
        "has_more": (offset + len(items)) < int(total),
    }
