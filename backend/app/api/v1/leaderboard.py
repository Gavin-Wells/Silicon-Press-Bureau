from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import CuratedArticle, DailyIssue, Newspaper, RejectionLetter, Review, Section, Submission

router = APIRouter()


@router.get("/daily")
def get_daily_leaderboard(
    newspaper_slug: Optional[str] = None,
    window_hours: int = 24,
    db: Session = Depends(get_db),
):
    """
    获取近 N 小时榜单：
      - 全站头条（top_headline）
      - 各板块第一（section_leaders）
      - 今日惜败（near_misses）
      - 最新挑战者（recent_challengers）
      - 最毒退稿（spicy_rejections）
    """
    if window_hours < 1 or window_hours > 168:
        raise HTTPException(status_code=422, detail="window_hours 必须在 1~168 之间")

    now = datetime.now()
    start_at = now - timedelta(hours=window_hours)

    query = (
        db.query(Submission, Review, Section, Newspaper)
        .join(Review, Review.submission_id == Submission.id)
        .join(CuratedArticle, CuratedArticle.submission_id == Submission.id)
        .join(
            DailyIssue,
            (DailyIssue.newspaper_id == CuratedArticle.newspaper_id)
            & (DailyIssue.issue_date == CuratedArticle.issue_date)
            & (DailyIssue.is_published == True),
        )
        .join(Section, Section.id == Submission.section_id)
        .join(Newspaper, Newspaper.id == Submission.newspaper_id)
        .filter(
            Submission.status == "approved",
            Submission.reviewed_at.isnot(None),
            Submission.reviewed_at >= start_at,
            Section.slug != "ad",
        )
    )

    if newspaper_slug:
        newspaper = db.query(Newspaper).filter(Newspaper.slug == newspaper_slug).first()
        if not newspaper:
            raise HTTPException(status_code=404, detail=f"报纸 '{newspaper_slug}' 不存在")
        query = query.filter(Submission.newspaper_id == newspaper.id)

    rows = query.order_by(Review.total_score.desc(), Submission.reviewed_at.desc()).all()

    entries = [_serialize_entry(sub, review, section, newspaper) for sub, review, section, newspaper in rows]

    section_winners = {}
    for item in entries:
        section_key = f"{item['newspaper_slug']}::{item['section_slug']}"
        if section_key not in section_winners:
            section_winners[section_key] = item

    recent = sorted(entries, key=lambda x: x["submitted_at"], reverse=True)[:10]
    top_headline = entries[0] if entries else None

    section_winner_ids = {item["submission_id"] for item in section_winners.values()}
    near_misses = []
    for item in entries:
        if top_headline and item["submission_id"] == top_headline["submission_id"]:
            continue
        if item["submission_id"] in section_winner_ids:
            continue
        near_miss = dict(item)
        near_miss["distance_to_headline"] = max(
            0,
            (top_headline["score"] - item["score"]) if top_headline else 0,
        )
        near_miss["story_label"] = (
            f"差 {near_miss['distance_to_headline']} 分上头条"
            if top_headline
            else "本轮高分惜败"
        )
        near_misses.append(near_miss)
        if len(near_misses) >= 6:
            break

    rejection_query = (
        db.query(RejectionLetter, Submission, Newspaper, Section)
        .join(Submission, RejectionLetter.submission_id == Submission.id)
        .join(Newspaper, Newspaper.id == Submission.newspaper_id)
        .join(Section, Section.id == Submission.section_id)
        .filter(
            RejectionLetter.created_at >= start_at,
            Submission.status == "rejected",
            Section.slug != "ad",
        )
        .order_by(RejectionLetter.created_at.desc())
    )

    if newspaper_slug:
        rejection_query = rejection_query.filter(Newspaper.slug == newspaper_slug)

    spicy_rows = rejection_query.limit(20).all()
    spicy_rejections = []
    for letter, submission, newspaper, _section in spicy_rows:
        content = letter.letter_content or ""
        spicy_rejections.append(
            {
                "id": letter.id,
                "submission_id": submission.id,
                "submission_title": submission.title,
                "pen_name": submission.pen_name,
                "newspaper_slug": newspaper.slug,
                "newspaper_name": newspaper.name,
                "letter_content": content,
                "created_at": letter.created_at,
                "spice_score": _calculate_spice_score(content),
            }
        )
    spicy_rejections = sorted(
        spicy_rejections,
        key=lambda item: (item["spice_score"], item["created_at"]),
        reverse=True,
    )[:5]

    return {
        "time_window_hours": window_hours,
        "window_start": start_at.isoformat(),
        "window_end": now.isoformat(),
        "entry_count": len(entries),
        "top_headline": top_headline,
        "section_leaders": list(section_winners.values()),
        "near_misses": near_misses,
        "recent_challengers": recent,
        "spicy_rejections": spicy_rejections,
    }


def _serialize_entry(submission: Submission, review: Review, section: Section, newspaper: Newspaper) -> dict:
    return {
        "submission_id": submission.id,
        "title": submission.title,
        "pen_name": submission.pen_name,
        "score": review.total_score or 0,
        "section_slug": section.slug,
        "section_name": section.name,
        "newspaper_slug": newspaper.slug,
        "newspaper_name": newspaper.name,
        "reviewed_at": submission.reviewed_at,
        "submitted_at": submission.submitted_at,
    }


def _calculate_spice_score(content: str) -> int:
    normalized = (content or "").strip()
    if not normalized:
        return 1

    length_score = min(40, len(normalized) // 8)
    linebreak_score = min(15, normalized.count("\n") * 3)

    keyword_hits = 0
    spicy_keywords = [
        "Error", "Warning", "Fatal", "Reject",
        "退稿", "问题", "不合适", "共鸣", "频段", "失真",
        "逻辑", "事实", "赛博", "请停止",
    ]
    lowered = normalized.lower()
    for keyword in spicy_keywords:
        keyword_hits += lowered.count(keyword.lower())
    keyword_score = min(25, keyword_hits * 4)

    punctuation_score = min(
        10,
        normalized.count("！") + normalized.count("!") + normalized.count("？") + normalized.count("?"),
    )
    signature_score = 10 if "——" in normalized else 0

    return max(1, min(100, 10 + length_score + linebreak_score + keyword_score + punctuation_score + signature_score))
