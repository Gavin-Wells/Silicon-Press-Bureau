"""
清理已入库 CuratedArticle 与 DailyIssue.layout_data 中的「新标题」「新内容」字样

与 reviewer.py 中解析逻辑一致：若标题/正文首行为「新标题」或「新内容」，去掉该行保留其余。
运行（在 backend 目录下）:
  python -m scripts.fix_curated_label_lines
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm.attributes import flag_modified

from app.core.database import SessionLocal
from app.models import CuratedArticle, DailyIssue


def drop_label_block(text: str | None, label: str) -> str:
    if not text or not text.strip():
        return text or ""
    first_line = (text.split("\n")[0] or "").strip()
    if first_line == label or first_line.startswith(label + "：") or first_line.startswith(label + ":"):
        rest = text.split("\n", 1)[1] if "\n" in text else ""
        return rest.strip() or text
    return text


def main():
    db = SessionLocal()
    try:
        # 1) 清理 CuratedArticle
        rows = db.query(CuratedArticle).all()
        updated_curated = 0
        for row in rows:
            new_title = drop_label_block(row.edited_title, "新标题")
            new_content = drop_label_block(row.edited_content, "新内容")
            if new_title != (row.edited_title or "") or new_content != (row.edited_content or ""):
                row.edited_title = new_title or row.edited_title
                row.edited_content = new_content or row.edited_content
                updated_curated += 1
        db.commit()
        print(f"[curated] 共 {len(rows)} 条选稿，已清理 {updated_curated} 条的「新标题/新内容」首行。")

        # 2) 清理 DailyIssue.layout_data 中缓存的 title/content
        issues = db.query(DailyIssue).all()
        updated_issues = 0
        for issue in issues:
            layout = issue.layout_data
            if not layout or not isinstance(layout, dict):
                continue
            pages = layout.get("pages") or []
            changed = False
            for page in pages:
                for col in page.get("columns") or []:
                    for item in col.get("items") or []:
                        if item.get("type") != "article":
                            continue
                        if "title" in item:
                            new_title = drop_label_block(item["title"], "新标题")
                            if new_title != item["title"]:
                                item["title"] = new_title
                                changed = True
                        if "content" in item:
                            new_content = drop_label_block(item["content"], "新内容")
                            if new_content != item["content"]:
                                item["content"] = new_content
                                changed = True
            if changed:
                flag_modified(issue, "layout_data")
                updated_issues += 1
        db.commit()
        print(f"[layout] 共 {len(issues)} 期版面，已清理 {updated_issues} 期的 layout_data 内「新标题/新内容」。")
        print("[done] 修复完成。")
    finally:
        db.close()


if __name__ == "__main__":
    main()
