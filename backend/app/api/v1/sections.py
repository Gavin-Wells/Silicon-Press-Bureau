"""
板块 API — /api/v1/sections

只读接口，供前端获取板块配置。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.newspaper_config import get_newspaper, get_sections, serialize_section

router = APIRouter()


@router.get("/{newspaper_slug}")
def list_sections(newspaper_slug: str, submittable_only: bool = True, db: Session = Depends(get_db)):
    """获取某份报纸的板块列表

    Args:
        newspaper_slug: 报纸标识
        submittable_only: 是否只返回可投稿板块 (默认 True)
    """
    if not get_newspaper(db, newspaper_slug):
        raise HTTPException(status_code=404, detail=f"报纸 '{newspaper_slug}' 不存在")
    sections = get_sections(db, newspaper_slug, submittable_only=submittable_only)

    return [
        {
            "slug": s["slug"],
            "name": s["name"],
            "description": s["description"],
            "min_chars": s["min_chars"],
            "max_chars": s["max_chars"],
            "scoring_dimensions": [
                {"name": d["name"], "weight": d["weight"], "description": d["description"]}
                for d in s["scoring_dimensions"]
            ]
        }
        for s in [serialize_section(section) for section in sections]
    ]
