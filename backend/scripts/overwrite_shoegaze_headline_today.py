"""
用「模拟真实用户投稿」覆盖《AI早报》今日头版头条（面向宝妈、具体真实）

先创建一条已过审的 Submission（真实感笔名与内容），再将今日头条 CuratedArticle
关联到该投稿，并同步更新当日 DailyIssue.layout_data，使前端显示为用户来稿。

运行（在 backend 目录下）:
  python -m scripts.overwrite_shoegaze_headline_today
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm.attributes import flag_modified

from app.core.database import SessionLocal
from app.core.timezone import shanghai_today
from app.models import CuratedArticle, DailyIssue, Newspaper, Section
from app.services.submission_pipeline import create_submission_record


# 模拟真实用户投稿：口语化、个人经历感、笔名像真人
PEN_NAME = "小满妈妈"
SHOEGAZE_HEADLINE_TITLE = "孩子睡觉后我拿 AI 搞副业，这几个路子真的有人赚到"

SHOEGAZE_HEADLINE_CONTENT = """我是二胎妈妈，白天带娃晚上想给自己留点时间，又不想纯刷手机。去年开始琢磨用 AI 做点能变现的事，也问了一圈身边的姐妹和群里的宝妈，把几个真的看到钱的路子整理了一下，不保证你也能赚到，但都是我能查到、有人真实在做的。

第一个是育儿号。我有个朋友用灵感岛那种 AI 写育儿文案，发抖音和小红书，粉丝做到 10 万以后开始接广告和直播。她跟我说单条广告 3000 到 8000 都有，直播分成好的时候一场能拿一两万，她上个月光这块就 4 万多。关键是做自己本来就懂的，带娃辅食早教这些，用 AI 只是省时间日更，别从零学一个完全不懂的。

第二个是头条。有个姐妹不会写长文，就用 DeepSeek 生成那种问答，截图或者整理成文章发今日头条。她有一篇讲暴利行业的，24 小时就 1200 多收益，那个月总共 7000 多。适合每天能挤一两个小时、能坚持发的人，上班的也能搞。

第三个是 AI 口播。不露脸，用 AI 做虚拟形象讲情感啊成长啊那种，我群里有人在做，说月入稳定在一万六左右，每天 500 多。要研究下平台规则和起号，但不用自己出镜我觉得挺适合社恐宝妈。

第四个是国外一个妈妈把女儿涂鸦做成 T 恤马克杯在 Etsy 卖，九个月赚了二十多万美金，每周只干十小时。国内可以对着淘宝闲鱼小红书做定制，用 AI 做图写详情页，宝妈带娃+创作本身就有故事好讲。

总结就是都在用 AI 省时间、做自己懂或很快能上手的，没有一夜暴富，但有具体数字。我觉得再晚一步跟不上的不是 AI，是你有没有先把「每天一小时」定下来。分享给姐妹们，有在做的可以一起交流。"""


def main():
    today = shanghai_today()
    db = SessionLocal()
    try:
        paper = db.query(Newspaper).filter(Newspaper.slug == "shoegaze").first()
        if not paper:
            print("[error] 未找到报刊 shoegaze（AI早报）")
            return

        section = (
            db.query(Section)
            .filter(Section.newspaper_id == paper.id)
            .order_by(Section.sort_order.asc(), Section.id.asc())
            .first()
        )
        if not section:
            print("[error] 未找到 AI早报 任一板块")
            return

        # 1) 模拟真实用户投稿：创建一条已过审的 Submission
        submission = create_submission_record(
            db,
            newspaper_id=paper.id,
            section_id=section.id,
            title=SHOEGAZE_HEADLINE_TITLE,
            content=SHOEGAZE_HEADLINE_CONTENT,
            pen_name=PEN_NAME,
            user_id=None,
            contact_email=None,
            status="approved",
        )
        db.flush()
        print(f"[submission] 已创建模拟投稿 id={submission.id}，笔名「{PEN_NAME}」")

        issue = (
            db.query(DailyIssue)
            .filter(
                DailyIssue.newspaper_id == paper.id,
                DailyIssue.issue_date == today,
            )
            .first()
        )
        first_item_id = None
        if issue and issue.layout_data:
            for page in issue.layout_data.get("pages") or []:
                for col in page.get("columns") or []:
                    for item in col.get("items") or []:
                        if item.get("type") == "article":
                            first_item_id = item.get("id")
                            break
                    if first_item_id is not None:
                        break
                if first_item_id is not None:
                    break

        headline = None
        if isinstance(first_item_id, int):
            headline = (
                db.query(CuratedArticle)
                .filter(
                    CuratedArticle.id == first_item_id,
                    CuratedArticle.newspaper_id == paper.id,
                    CuratedArticle.issue_date == today,
                )
                .first()
            )
        if not headline:
            headline = (
                db.query(CuratedArticle)
                .filter(
                    CuratedArticle.newspaper_id == paper.id,
                    CuratedArticle.issue_date == today,
                    CuratedArticle.importance == "headline",
                )
                .first()
            )
        if not headline:
            headline = (
                db.query(CuratedArticle)
                .filter(
                    CuratedArticle.newspaper_id == paper.id,
                    CuratedArticle.issue_date == today,
                )
                .order_by(CuratedArticle.id.asc())
                .first()
            )

        if not headline:
            db.rollback()
            print(f"[error] 未找到《AI早报》今日({today}) 任何选稿，无法挂接投稿。")
            return

        # 2) 将今日头条关联到该投稿（显示为真实用户来稿）
        headline.submission_id = submission.id
        headline.section_id = section.id
        headline.importance = "headline"
        headline.edited_title = submission.title
        headline.edited_content = submission.content
        headline.editor_note = ""
        db.commit()
        print(f"[curated] 头条 id={headline.id} 已关联投稿 id={submission.id}，作者={PEN_NAME}")

        if issue and issue.layout_data:
            layout = issue.layout_data
            hit = False
            for page in layout.get("pages") or []:
                for col in page.get("columns") or []:
                    for item in col.get("items") or []:
                        if item.get("type") == "article":
                            item["title"] = submission.title
                            item["content"] = submission.content
                            item["author"] = PEN_NAME
                            hit = True
                            break
                    if hit:
                        break
                if hit:
                    break
            if hit:
                flag_modified(issue, "layout_data")
                db.commit()
                print("[layout] 已同步更新当日版面头条（标题、正文、作者）。")
        else:
            print("[warn] 当日无版面或 layout_data 为空，仅已更新选稿表。")

        print("[done] AI早报今日头条已改为模拟真实用户投稿。")
    finally:
        db.close()


if __name__ == "__main__":
    main()
