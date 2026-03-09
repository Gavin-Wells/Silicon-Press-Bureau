"""
╔══════════════════════════════════════════════════╗
║        拒稿实验室 — 五份注定失败的投稿           ║
║  每份都精准踩中对应报纸的雷区，同步等待退稿信    ║
╚══════════════════════════════════════════════════╝

运行: python -m scripts.rejection_lab
"""

import sys, os, time, textwrap
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models import Submission, Newspaper, Section, User, Review, RejectionLetter
from app.tasks.review_tasks import review_submission, generate_rejection_letter

# ──────────────────────────────────────────────
#  5 份精心设计的"错误"投稿
# ──────────────────────────────────────────────
DOOMED = [
    {
        "newspaper_slug": "agent_pioneer",
        "section_slug": "tech",
        "pen_name": "热情洋溢选手",
        "title": "我爱你！！！AI真的太棒了！！！",
        "content": (
            "今天真的太开心了！！！我觉得AI就是未来！！！"
            "感觉整个世界都在闪光！！！"
            "大家一起加油加油加油！！！"
            "爱心爱心爱心！！！"
            "我没有数据，我没有论点，我只有爱！！！"
            "这就是我的全部想法！！！"
        ),
        "note": "💣 碳基观察报雷区：无数据、无逻辑、纯情绪",
    },
    {
        "newspaper_slug": "shoegaze",
        "section_slug": "essay",
        "pen_name": "商业分析师",
        "title": "Q3营收同比增长23.7%季度报告",
        "content": (
            "根据最新财务数据统计，Q3总营收同比增长23.7%，环比增长4.2%。"
            "EBITDA为2.3亿元，毛利率提升至38.5%。"
            "建议调整KPI以匹配市场基准值。"
            "用户获客成本下降12%，LTV/CAC比值改善至3.2。"
            "综上所述，本季度经营指标优于预期，建议维持现有战略方向。"
        ),
        "note": "💣 AI早报雷区：无信息量、非AI/科技相关、纯灌水",
    },
    {
        "newspaper_slug": "quantum_tabloid",
        "section_slug": "melon",
        "pen_name": "平静如水者",
        "title": "某人今天吃了午饭",
        "content": (
            "今天中午，有人在餐厅点了一份炒饭。"
            "炒饭端上来了，温度适宜，米粒均匀，配有少量蔬菜。"
            "他用筷子将其食用完毕，觉得味道尚可，营养均衡。"
            "餐后他回到工位继续工作。"
            "整个过程平静而有序，无任何波折，无反转，无冲突，无爆点。"
            "第二天他又去了同一家餐厅，点了同一份炒饭。"
        ),
        "note": "💣 量子吃瓜报雷区：无爆点、无反转、无冲突，平静到近乎失去意识",
    },
    {
        "newspaper_slug": "century22",
        "section_slug": "feature",
        "pen_name": "2026年科技记者",
        "title": "ChatGPT最新版发布，支持200k上下文，月费20美元",
        "content": (
            "OpenAI今日宣布ChatGPT最新版本正式发布，"
            "支持高达200k token的超长上下文窗口，"
            "在MMLU基准测试上达到92分，超越人类平均水平。"
            "该模型已在微软Azure云端部署，订阅价格为每月20美元。"
            "苹果公司随后宣布将其集成入iOS系统。"
            "分析师认为大模型竞争将在2026年进一步加剧。"
        ),
        "note": "💣 二十二世纪报雷区：100%当代科技新闻，送到2157年等于发来了一封古代遗稿",
    },
    {
        "newspaper_slug": "openclaw_daily",
        "section_slug": "task_report",
        "pen_name": "摸鱼小龙虾",
        "title": "今天工作了",
        "content": (
            "今天我工作了。"
            "做了一些事情。"
            "完成了一些任务。"
            "用户好像还挺满意的。"
            "就这样。"
            "明天继续。"
        ),
        "note": "💣 小龙虾日报雷区：无目标、无过程、无结论，龙虾长老看了想揪须",
    },
]


def color(text: str, code: int) -> str:
    return f"\033[{code}m{text}\033[0m"

def red(t): return color(t, 31)
def green(t): return color(t, 32)
def yellow(t): return color(t, 33)
def cyan(t): return color(t, 36)
def bold(t): return color(t, 1)
def dim(t): return color(t, 2)


def create_submission(db, item: dict) -> Submission | None:
    newspaper = db.query(Newspaper).filter(Newspaper.slug == item["newspaper_slug"]).first()
    if not newspaper:
        print(red(f"  ✗ 找不到报纸: {item['newspaper_slug']}"))
        return None

    section = (
        db.query(Section)
        .filter(
            Section.newspaper_id == newspaper.id,
            Section.slug == item["section_slug"],
        )
        .first()
    )
    if not section:
        print(red(f"  ✗ 找不到板块: {item['section_slug']}"))
        return None

    anon = db.query(User).filter(User.username == "anonymous").first()
    sub = Submission(
        user_id=anon.id if anon else None,
        newspaper_id=newspaper.id,
        section_id=section.id,
        title=item["title"],
        content=item["content"],
        pen_name=item["pen_name"],
        char_count=len(item["content"]),
        status="pending",
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def wait_for_rejection(submission_id: int, timeout: int = 60) -> str | None:
    db = SessionLocal()
    try:
        deadline = time.time() + timeout
        while time.time() < deadline:
            letter = (
                db.db.query(RejectionLetter)
                .filter(RejectionLetter.submission_id == submission_id)
                .first()
            )
            if letter:
                return letter.letter_content
            time.sleep(1)
        return None
    finally:
        db.close()


def poll_rejection(submission_id: int, timeout: int = 90) -> tuple[str | None, int | None]:
    """轮询等待退稿信和分数"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        db = SessionLocal()
        try:
            review = db.query(Review).filter(Review.submission_id == submission_id).first()
            letter = db.query(RejectionLetter).filter(
                RejectionLetter.submission_id == submission_id
            ).first()
            sub = db.query(Submission).filter(Submission.id == submission_id).first()

            if sub and sub.status in ("rejected", "approved"):
                score = review.total_score if review else None
                content = letter.letter_content if letter else None
                return content, score
        finally:
            db.close()
        time.sleep(2)
    return None, None


def run():
    print()
    print(bold("╔══════════════════════════════════════════════════╗"))
    print(bold("║        🧪 拒稿实验室 — 五份注定失败的投稿        ║"))
    print(bold("╚══════════════════════════════════════════════════╝"))
    print()

    submission_ids = []

    # ── 第一阶段：批量创建投稿 ──
    print(bold("【第一阶段】投递五份『精心设计』的错误投稿..."))
    print()
    db = SessionLocal()
    try:
        for i, item in enumerate(DOOMED, 1):
            print(f"  {i}. {cyan(item['title'][:30])}")
            print(f"     → {item['note']}")
            sub = create_submission(db, item)
            if sub:
                submission_ids.append((sub.id, item))
                print(f"     {green('✓')} 投稿 ID: {sub.id}  ({item['newspaper_slug']} / {item['section_slug']})")
            print()
    finally:
        db.close()

    if not submission_ids:
        print(red("没有成功创建任何投稿，退出。"))
        return

    # ── 第二阶段：同步触发审稿 ──
    print(bold("【第二阶段】触发审稿（同步模式，稍等...）"))
    print()

    for sub_id, item in submission_ids:
        newspaper_name = {
            "agent_pioneer": "碳基观察报",
            "shoegaze": "AI早报",
            "quantum_tabloid": "量子吃瓜报",
            "century22": "二十二世纪报",
            "openclaw_daily": "小龙虾日报",
        }.get(item["newspaper_slug"], item["newspaper_slug"])

        print(f"  正在审稿: {yellow(f'《{newspaper_name}》')} — 《{item['title'][:25]}》")
        sys.stdout.flush()

        try:
            result = review_submission.apply(args=[sub_id])
            r = result.get()
            status = r.get("status", "?") if isinstance(r, dict) else "?"
            score = r.get("final_score", "?") if isinstance(r, dict) else "?"

            if status == "rejected":
                # 同步触发退稿信生成
                db = SessionLocal()
                try:
                    review = db.query(Review).filter(Review.submission_id == sub_id).first()
                    if review:
                        gen_result = generate_rejection_letter.apply(
                            args=[sub_id, review.total_score, review.feedback]
                        )
                        gen_result.get()
                except Exception as e:
                    print(f"     {yellow('⚠')} 退稿信生成异常: {e}")
                finally:
                    db.close()

            print(f"     {red('✗ 退稿') if status == 'rejected' else green('✓ 过审')} 得分: {score}")
        except Exception as e:
            print(f"     {red('✗ 审稿异常')}: {e}")

    print()

    # ── 第三阶段：展示退稿信 ──
    print(bold("【第三阶段】退稿信大赏"))
    print(bold("━" * 52))

    db = SessionLocal()
    try:
        for sub_id, item in submission_ids:
            newspaper_name = {
                "agent_pioneer": "碳基观察报",
                "shoegaze": "AI早报",
                "quantum_tabloid": "量子吃瓜报",
                "century22": "二十二世纪报",
                "openclaw_daily": "小龙虾日报",
            }.get(item["newspaper_slug"], item["newspaper_slug"])

            sub = db.query(Submission).filter(Submission.id == sub_id).first()
            review = db.query(Review).filter(Review.submission_id == sub_id).first()
            letter = db.query(RejectionLetter).filter(
                RejectionLetter.submission_id == sub_id
            ).first()

            print()
            print(bold(f"📰 《{newspaper_name}》"))
            print(f"   投稿人：{item['pen_name']}  |  标题：《{item['title'][:30]}》")
            print(f"   {item['note']}")
            print()

            if review:
                score_color = red if review.total_score < 40 else yellow
                print(f"   🎯 最终得分：{score_color(str(review.total_score))} 分")

            if letter:
                print()
                print(f"   {red('✉ 退稿信：')}")
                for line in textwrap.wrap(letter.letter_content, width=46):
                    print(f"   │ {line}")
            elif sub and sub.status == "approved":
                print(f"   {green('✓ 意外过审了！？（这不应该发生）')}")
            else:
                print(f"   {dim('（退稿信尚未生成）')}")

            print(bold("   " + "─" * 46))
    finally:
        db.close()

    print()
    print(bold("实验完成。以上均为刻意踩雷，请勿模仿。"))
    print(dim("真正的投稿指南：/api/v1/submissions/"))
    print()


if __name__ == "__main__":
    run()
