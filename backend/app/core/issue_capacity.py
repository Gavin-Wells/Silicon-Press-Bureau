from typing import List

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import Newspaper
from app.services.newspaper_config import get_effective_newspaper_config

def get_issue_quotas(newspaper_slug: str, db: Session | None = None) -> List[dict]:
    owns_session = db is None
    db = db or SessionLocal()
    try:
        newspaper = db.query(Newspaper).filter(Newspaper.slug == newspaper_slug).first()
        if not newspaper:
            raise RuntimeError(f"报刊 '{newspaper_slug}' 不存在")
        config = get_effective_newspaper_config(db, newspaper=newspaper)
        return config["issue_config"]
    finally:
        if owns_session:
            db.close()


def get_newspaper_publish_capacity(newspaper_slug: str, db: Session | None = None) -> int:
    pages = get_issue_quotas(newspaper_slug, db=db)
    total = 0
    for page in pages:
        quota = page.get("quota") or {}
        total += int(quota.get("headline", 0)) + int(quota.get("secondary", 0)) + int(quota.get("brief", 0))
    return max(1, total)


def get_newspaper_approved_pool_cap(newspaper_slug: str, db: Session | None = None) -> int:
    pages = get_issue_quotas(newspaper_slug, db=db)
    total = 0
    for page in pages:
        total += max(1, int(page.get("approved_pool_cap", 0)))
    return max(1, total)
