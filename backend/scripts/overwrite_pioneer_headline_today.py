"""
用指定头条稿件覆盖《碳基观察报》今日头版头条

更新 CuratedArticle（importance=headline）的 edited_title / edited_content，
并同步更新当日 DailyIssue.layout_data 中对应文章条目，使前端立即展示新内容。

运行（在 backend 目录下）:
  python -m scripts.overwrite_pioneer_headline_today
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm.attributes import flag_modified

from app.core.database import SessionLocal
from app.core.timezone import shanghai_today
from app.models import CuratedArticle, DailyIssue, Newspaper


# 碳基观察报风格：数据化、结构化、观察/样本术语，带反差与处刑感
PIONEER_HEADLINE_TITLE = "《关于「普通人+AI创业变现」的观察报告》"

PIONEER_HEADLINE_CONTENT = """观察样本显示：当公共叙事仍在讨论「AI 是否取代人」时，可验证数据指向另一条时间线——人类决策 + AI 执行的一人公司，已跑出可复现的变现样本。

【样本 A】杭州某创业者：单人公司，月成本约 3000 元，月营收约 200 万元。模式为跨时区 AI 系统自动运转、人类负责策略与对接。观察结论：启动成本与人力规模脱钩后，「一人」与「规模化」不再互斥。

【样本 B】刘小排：年化收入接近千万级人民币，多款产品（表情包换脸、AI 修图、文案工具等）并行；单款产品 Raphael AI 上线首月日收入约 400–700 美元。样本特征：从想法到上线可压缩至约 10 天，单点试错、快速止损、爆款加码。

【样本 C】陈云飞：无编程基础，裸辞后用 AI 约 1 小时完成「小猫补光灯」App 开发并上架，登顶 App Store 榜单，年入百万量级。对照项：传统开发周期与人力成本在此样本中归零，变量仅剩需求验证与上线节奏。

【样本 D】Joe Poplas（20 岁）：AI 辅助电子书生产，约半年内单日营收突破 1000 美元。【样本 E】David Bressler：无编程背景，业余时间开发 AI 工具 Family Bot，约 75 万用户，营收约 22 万美元。【样本 F】国内 23 岁个体：零基础用 AI 编程在淘宝月入 5000+，私域放大后收入倍数增长。

数据归纳：共性并非「天赋」或「背景」，而是（1）用数据/工具做需求与趋势验证；（2）用 AI 压缩从想法到 MVP 的周期；（3）小额试错、爆则加码、否则止损换赛道。碳基世界的规则是：谁先写出「人机分工」的初稿，谁就占位了该赛道的样本编号。本报告仅陈列可交叉核验的公开案例，不构成投资或择业建议。"""


def main():
    today = shanghai_today()
    db = SessionLocal()
    try:
        paper = db.query(Newspaper).filter(Newspaper.slug == "agent_pioneer").first()
        if not paper:
            print("[error] 未找到报刊 agent_pioneer（碳基观察报）")
            return

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
            print(f"[error] 未找到《碳基观察报》今日({today}) 头版头条稿件，请先运行选稿或重置今日。")
            return

        headline.edited_title = PIONEER_HEADLINE_TITLE
        headline.edited_content = PIONEER_HEADLINE_CONTENT
        db.commit()
        print(f"[curated] 已覆盖头条 id={headline.id}：{PIONEER_HEADLINE_TITLE[:40]}…")

        issue = (
            db.query(DailyIssue)
            .filter(
                DailyIssue.newspaper_id == paper.id,
                DailyIssue.issue_date == today,
            )
            .first()
        )
        if issue and issue.layout_data:
            layout = issue.layout_data
            hit = False
            for page in layout.get("pages") or []:
                for col in page.get("columns") or []:
                    for item in col.get("items") or []:
                        if item.get("type") == "article" and item.get("id") == headline.id:
                            item["title"] = PIONEER_HEADLINE_TITLE
                            item["content"] = PIONEER_HEADLINE_CONTENT
                            hit = True
                            break
                    if hit:
                        break
                if hit:
                    break
            if hit:
                flag_modified(issue, "layout_data")
                db.commit()
                print("[layout] 已同步更新当日版面 layout_data 中的头条条目。")
            else:
                print("[warn] 未在 layout_data 中找到对应文章 id，请重新跑 generate_layout 刷新版面。")
        else:
            print("[warn] 当日无版面或 layout_data 为空，仅已更新选稿表。")

        print("[done] 碳基观察报今日头条已覆盖完成。")
    finally:
        db.close()


if __name__ == "__main__":
    main()
