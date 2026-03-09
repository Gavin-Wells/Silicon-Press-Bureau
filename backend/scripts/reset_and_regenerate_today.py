"""
重置并重新生成「今天」的版面

步骤：
1. 删除今日已选稿（CuratedArticle）与今日版面（DailyIssue）
2. 对「今天」执行选稿（含邀稿，结合时事/反差/焦虑/搞钱等配置）
3. 生成今日 layout
4. 发布今日 issue

运行（在 backend 目录下）:
  python -m scripts.reset_and_regenerate_today
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.core.timezone import shanghai_today
from app.models import CuratedArticle, DailyIssue


def main():
    today = shanghai_today()
    db = SessionLocal()
    try:
        # 1) 删除今日 CuratedArticle
        deleted_curated = (
            db.query(CuratedArticle)
            .filter(CuratedArticle.issue_date == today)
            .delete()
        )
        # 2) 删除今日 DailyIssue
        deleted_issues = (
            db.query(DailyIssue)
            .filter(DailyIssue.issue_date == today)
            .delete()
        )
        db.commit()
        print(f"[reset] 已删除今日({today}) 选稿 {deleted_curated} 条、版面 {deleted_issues} 期")
    finally:
        db.close()

    # 3) 对「今天」执行选稿（邀稿会使用 newspaper_config 里的时事/反差/焦虑/搞钱等配置）
    from app.tasks.curation_tasks import curate_daily_articles

    print("[curate] 开始为今日选稿与邀稿…")
    curate_result = curate_daily_articles.apply(
        kwargs={"target_issue_date": today.isoformat()}
    ).get()
    for r in curate_result:
        print(
            f"  {r['newspaper']}: curated={r.get('curated', 0)}, invited={r.get('invited', 0)}, issue_date={r.get('issue_date')}"
        )

    # 4) 生成今日 layout
    from app.tasks.publish_tasks import generate_layout

    print("[layout] 生成今日版面…")
    layout_result = generate_layout.apply().get()
    for r in layout_result:
        print(f"  {r['newspaper']}: issue_number={r.get('issue_number')}, article_count={r.get('article_count')}")

    # 5) 发布今日 issue
    from app.tasks.publish_tasks import publish_issue

    print("[publish] 发布今日报纸…")
    publish_result = publish_issue.apply().get()
    print(f"  已发布 {publish_result.get('published_count', 0)} 期，日期 {publish_result.get('date')}")

    print(f"[done] 今日({today}) 已重置并重新生成、发布完成。")


if __name__ == "__main__":
    main()
