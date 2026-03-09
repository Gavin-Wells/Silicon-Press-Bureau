from datetime import date

import redis
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models import RejectionLetter, Review, Submission
from app.services.anti_spam import ensure_anon_id

router = APIRouter()
redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


@router.get("/overview")
def get_overview_stats(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    首页概览指标：
      - 今日投稿数
      - 已审稿过稿率
      - 今日退稿信数
      - 访问人数（去重）
    """
    today = date.today()

    today_submissions = (
        db.query(func.count(Submission.id))
        .filter(func.date(Submission.submitted_at) == today)
        .scalar()
        or 0
    )

    reviewed_total = db.query(func.count(Review.id)).scalar() or 0
    approved_total = (
        db.query(func.count(Submission.id))
        .join(Review, Review.submission_id == Submission.id)
        .filter(Submission.status == "approved")
        .scalar()
        or 0
    )
    approval_rate = round((approved_total / reviewed_total) * 100) if reviewed_total else 0

    today_rejections = (
        db.query(func.count(RejectionLetter.id))
        .filter(func.date(RejectionLetter.created_at) == today)
        .scalar()
        or 0
    )

    pending_total = (
        db.query(func.count(Submission.id))
        .filter(Submission.status.in_(["pending", "reviewing", "queued_overflow"]))
        .scalar()
        or 0
    )

    # 访问人数：按匿名访客 ID 去重（all-time + 今日）
    total_visitors = 0
    today_visitors = 0
    try:
        anon_id = ensure_anon_id(request, response)
        all_key = "stats:visitors:all"
        day_key = f"stats:visitors:day:{today.isoformat()}"
        redis_client.sadd(all_key, anon_id)
        redis_client.sadd(day_key, anon_id)
        # 今日集合保留 8 天，避免无穷增长
        redis_client.expire(day_key, 60 * 60 * 24 * 8)
        total_visitors = int(redis_client.scard(all_key) or 0)
        today_visitors = int(redis_client.scard(day_key) or 0)
    except redis.RedisError:
        # Redis 异常时降级为 0，不影响首页主流程
        total_visitors = 0
        today_visitors = 0

    return {
        "today_submissions": today_submissions,
        "approval_rate": approval_rate,
        "today_rejections": today_rejections,
        "pending_total": pending_total,
        "total_visitors": total_visitors,
        "today_visitors": today_visitors,
    }
