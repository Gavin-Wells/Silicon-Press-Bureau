from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.timezone import shanghai_today
from app.models import Newspaper, DailyIssue, CuratedArticle, Section
from app.schemas import NewspaperResponse, LiveIssueResponse, IssueMetaResponse

router = APIRouter()

PRIORITY_NEWSPAPER_SLUGS = {
    "shoegaze": 0,
    "openclaw_daily": 1,
    "the_red_claw": 2,
}


def _is_preview_admin(admin_user: Optional[str]) -> bool:
    """判断是否具备明日预览权限（由配置控制，不硬编码用户名）。"""
    user = (admin_user or "").strip().lower()
    if not user:
        return False
    allowed = {
        item.strip().lower()
        for item in settings.PREVIEW_ADMIN_USERS.split(",")
        if item.strip()
    }
    return user in allowed


@router.get("", response_model=List[NewspaperResponse])
def get_newspapers(db: Session = Depends(get_db)):
    rows = (
        db.query(Newspaper)
        .order_by(Newspaper.id.asc())
        .all()
    )
    rows.sort(key=lambda row: (PRIORITY_NEWSPAPER_SLUGS.get(row.slug, 999), row.id))
    # 兼容历史脏数据，避免响应模型校验报 500。
    return [
        NewspaperResponse(
            id=row.id,
            name=row.name,
            slug=row.slug,
            editor_name=row.editor_name or "编辑部",
            editor_persona=row.editor_persona,
            pass_threshold=row.pass_threshold or 60,
        )
        for row in rows
    ]


@router.get("/latest-live-all", response_model=Dict[str, LiveIssueResponse])
def get_all_latest_live_issues(
    compact: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    """
    一次返回所有报纸的最新已发布版面，供首页批量展示，减少 N 次请求。

    compact=true 时，仅返回头条摘要页，显著减少响应体大小与序列化时间。
    """
    newspapers = db.query(Newspaper).order_by(Newspaper.id.asc()).all()
    newspapers.sort(key=lambda row: (PRIORITY_NEWSPAPER_SLUGS.get(row.slug, 999), row.id))

    np_ids = [row.id for row in newspapers]
    if np_ids:
        latest_dates_subq = (
            db.query(
                DailyIssue.newspaper_id.label("newspaper_id"),
                func.max(DailyIssue.issue_date).label("latest_issue_date"),
            )
            .filter(
                DailyIssue.is_published == True,
                DailyIssue.newspaper_id.in_(np_ids),
            )
            .group_by(DailyIssue.newspaper_id)
            .subquery()
        )
        latest_issues = (
            db.query(DailyIssue)
            .join(
                latest_dates_subq,
                and_(
                    DailyIssue.newspaper_id == latest_dates_subq.c.newspaper_id,
                    DailyIssue.issue_date == latest_dates_subq.c.latest_issue_date,
                ),
            )
            .all()
        )
    else:
        latest_issues = []

    latest_by_np_id: Dict[int, DailyIssue] = {issue.newspaper_id: issue for issue in latest_issues}

    result: Dict[str, LiveIssueResponse] = {}
    for newspaper in newspapers:
        issue = latest_by_np_id.get(newspaper.id)
        if issue:
            payload = _serialize_live_issue(issue, newspaper)
            if compact:
                payload["pages"] = _compact_pages(payload.get("pages") or [])
            result[newspaper.slug] = LiveIssueResponse(**payload)
        else:
            result[newspaper.slug] = LiveIssueResponse(
                status="pending_publish",
                newspaper_slug=newspaper.slug,
                issue_meta=None,
                pages=[],
            )
    return result


@router.get("/{slug}/latest")
def get_latest_issue(slug: str, db: Session = Depends(get_db)):
    """
    兼容旧接口：返回 raw layout_data。
    新前端应使用 /latest-live。
    """
    newspaper = db.query(Newspaper).filter(Newspaper.slug == slug).first()
    if not newspaper:
        return {"error": "Newspaper not found"}

    issue = (
        db.query(DailyIssue)
        .filter(DailyIssue.newspaper_id == newspaper.id)
        .order_by(DailyIssue.issue_date.desc())
        .first()
    )

    return issue.layout_data if issue else {"articles": []}


@router.get("/{slug}/latest-live", response_model=LiveIssueResponse)
def get_latest_live_issue(
    slug: str,
    admin_user: Optional[str] = Query(default=None),
    include_tomorrow_preview: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    newspaper = db.query(Newspaper).filter(Newspaper.slug == slug).first()
    if not newspaper:
        raise HTTPException(status_code=404, detail="报纸不存在")

    if include_tomorrow_preview and _is_preview_admin(admin_user):
        tomorrow_issue_date = shanghai_today() + timedelta(days=1)
        tomorrow_issue = (
            db.query(DailyIssue)
            .filter(
                DailyIssue.newspaper_id == newspaper.id,
                DailyIssue.issue_date == tomorrow_issue_date,
            )
            .first()
        )
        if tomorrow_issue:
            payload = _serialize_live_issue(tomorrow_issue, newspaper)
            # 预览态：未发布也返回 pages，避免触发任何补稿/重排版。
            if not tomorrow_issue.is_published:
                payload["status"] = "pending_publish"
            return LiveIssueResponse(**payload)
        # 若明日 DailyIssue 尚未生成，则基于明日 curated_articles 组装只读预览
        curated_rows = (
            db.query(CuratedArticle)
            .filter(
                CuratedArticle.newspaper_id == newspaper.id,
                CuratedArticle.issue_date == tomorrow_issue_date,
            )
            .order_by(CuratedArticle.created_at.asc(), CuratedArticle.id.asc())
            .all()
        )
        section_map = {
            section.id: section.name
            for section in db.query(Section).filter(Section.newspaper_id == newspaper.id).all()
        }
        pages = _build_preview_pages_from_curated(curated_rows, section_map)
        return LiveIssueResponse(
            status="pending_publish",
            newspaper_slug=slug,
            issue_meta=IssueMetaResponse(
                newspaper_name=newspaper.name,
                newspaper_slug=newspaper.slug,
                issue_date=tomorrow_issue_date,
                issue_number=None,
                template_used="预览草稿",
                article_count=len(curated_rows),
                editor_message="管理员预览（未发布）",
                published_at=None,
            ),
            pages=pages,
        )

    issue = (
        db.query(DailyIssue)
        .filter(
            DailyIssue.newspaper_id == newspaper.id,
            DailyIssue.is_published == True,
        )
        .order_by(DailyIssue.issue_date.desc())
        .first()
    )

    if not issue:
        return LiveIssueResponse(
            status="pending_publish",
            newspaper_slug=slug,
            issue_meta=None,
            pages=[],
        )

    payload = _serialize_live_issue(issue, newspaper)
    return LiveIssueResponse(**payload)


@router.get("/{slug}/issues/{issue_date}", response_model=LiveIssueResponse)
def get_issue_by_date(slug: str, issue_date: date, db: Session = Depends(get_db)):
    newspaper = db.query(Newspaper).filter(Newspaper.slug == slug).first()
    if not newspaper:
        raise HTTPException(status_code=404, detail="报纸不存在")

    issue = (
        db.query(DailyIssue)
        .filter(
            DailyIssue.newspaper_id == newspaper.id,
            DailyIssue.issue_date == issue_date,
        )
        .first()
    )
    if not issue:
        raise HTTPException(status_code=404, detail="该日期报纸不存在")

    if not issue.is_published:
        return LiveIssueResponse(
            status="pending_publish",
            newspaper_slug=slug,
            issue_meta=IssueMetaResponse(
                newspaper_name=newspaper.name,
                newspaper_slug=newspaper.slug,
                issue_date=issue.issue_date,
                issue_number=issue.issue_number,
                template_used=issue.template_used,
                article_count=issue.article_count or 0,
                editor_message=issue.editor_message,
                published_at=None,
            ),
            pages=[],
        )

    payload = _serialize_live_issue(issue, newspaper)
    return LiveIssueResponse(**payload)


def _compact_pages(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """首页批量接口的轻量版 pages：仅返回一条最重要文章摘要。"""
    pick = _pick_primary_article(pages)
    if not pick:
        return []

    brief = {
        "type": "article",
        "id": pick.get("id"),
        "title": pick.get("title", ""),
        "content": _truncate_text(str(pick.get("content", "")), 220),
        "author": pick.get("author", "匿名"),
        "column": pick.get("column", "头版"),
        "importance": pick.get("importance", "brief"),
    }
    return [
        {
            "page_num": 1,
            "section_name": brief["column"] or "头版",
            "template_used": "首页摘要",
            "columns": [{"width": 1, "items": [brief]}],
        }
    ]


def _pick_primary_article(pages: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    fallback = None
    for page in pages:
        for col in page.get("columns", []):
            for item in col.get("items", []):
                if item.get("type") != "article":
                    continue
                if fallback is None:
                    fallback = item
                if item.get("importance") == "headline":
                    return item
    return fallback


def _truncate_text(text: str, max_len: int) -> str:
    clean = " ".join(text.split())
    if len(clean) <= max_len:
        return clean
    return clean[: max_len - 3].rstrip() + "..."


def _serialize_live_issue(issue: DailyIssue, newspaper: Newspaper) -> Dict[str, Any]:
    raw_pages = (issue.layout_data or {}).get("pages", [])
    pages = [_normalize_page(page) for page in raw_pages]

    return {
        "status": "published",
        "newspaper_slug": newspaper.slug,
        "issue_meta": {
            "newspaper_name": newspaper.name,
            "newspaper_slug": newspaper.slug,
            "issue_date": issue.issue_date,
            "issue_number": issue.issue_number,
            "template_used": issue.template_used,
            "article_count": issue.article_count or 0,
            "editor_message": issue.editor_message,
            "published_at": issue.published_at,
        },
        "pages": pages,
    }


def _normalize_page(page: Dict[str, Any]) -> Dict[str, Any]:
    columns = page.get("columns", [])
    normalized_columns = []

    for col in columns:
        items = col.get("items", [])
        normalized_items = [_normalize_item(item) for item in items]
        normalized_columns.append(
            {
                "width": col.get("width", 1),
                "items": normalized_items,
            }
        )

    return {
        "page_num": page.get("page_num", page.get("pageNum", 1)),
        "section_name": page.get("section_name", page.get("sectionName", "综合")),
        "template_used": page.get("template_used", page.get("templateUsed", "经典头版")),
        "columns": normalized_columns,
    }


def _normalize_item(item: Dict[str, Any]) -> Dict[str, Any]:
    item_type = item.get("type")
    if item_type in {"divider", "quote", "box", "ad"}:
        return item

    # 兼容旧 article 结构：没有 type 字段
    return {
        "type": "article",
        "id": item.get("id"),
        "title": item.get("title", ""),
        "content": item.get("content", ""),
        "author": item.get("author", "匿名"),
        "column": item.get("column", "综合"),
        "importance": item.get("importance", "brief"),
    }


def _build_preview_pages_from_curated(
    curated_rows: List[CuratedArticle],
    section_map: Dict[int, str],
) -> List[Dict[str, Any]]:
    if not curated_rows:
        return []

    importance_order = {"headline": 0, "secondary": 1, "brief": 2}
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for row in curated_rows:
        section_name = section_map.get(row.section_id, "综合")
        item = {
            "type": "article",
            "id": row.id,
            "title": row.edited_title or "无标题",
            "content": row.edited_content or "",
            "author": _resolve_preview_author(row),
            "column": section_name,
            "importance": row.importance if row.importance in importance_order else "brief",
        }
        grouped.setdefault(section_name, []).append(item)

    pages: List[Dict[str, Any]] = []
    for section_name, items in grouped.items():
        items.sort(key=lambda x: (importance_order.get(x["importance"], 3), x["id"]))
        pages.append(
            {
                "page_num": len(pages) + 1,
                "section_name": section_name,
                "template_used": "预览草稿",
                "columns": [
                    {"width": 1, "items": items},
                ],
            }
        )
    return pages


def _resolve_preview_author(curated: CuratedArticle) -> str:
    if curated.submission and curated.submission.pen_name:
        return curated.submission.pen_name
    return "匿名"
