import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.database import SessionLocal
from app.models import Submission, Newspaper, Section
from app.tasks.review_tasks import review_submission

def trigger_real_ai_rejections():
    db = SessionLocal()
    try:
        pioneer = db.query(Newspaper).filter(Newspaper.slug == "agent_pioneer").first()
        shoegaze = db.query(Newspaper).filter(Newspaper.slug == "shoegaze").first()
        
        pioneer_section = db.query(Section).filter(Section.newspaper_id == pioneer.id, Section.slug == "tech").first()
        shoegaze_section = db.query(Section).filter(Section.newspaper_id == shoegaze.id, Section.slug == "essay").first()

        # 准备一些容易被拒的“烂稿子”，让 AI 去真实批斗它们
        terrible_submissions = [
            # 投给理性派 Agent先锋报，但完全没有逻辑，纯情感宣泄
            {
                "newspaper": pioneer,
                "section": pioneer_section,
                "title": "我今天终于把代码删了，感觉好轻松",
                "content": "我受够了，那个类里面有一万行代码，根本看不懂。今天老板不在，我一气之下把它全删了，现在项目跑不起来了，但我心里觉得好轻松，这就是程序员的救赎吧！",
                "pen_name": "摆烂工程师"
            },
            # 投给理性派 Agent先锋报，毫无意义的灌水废话
            {
                "newspaper": pioneer,
                "section": pioneer_section,
                "title": "关于用Python写Hello World的十个心得",
                "content": "众所周知，print('Hello World') 是每个程序员的必经之路。今天我发现，如果你把单引号改成双引号，它一样能运行。而且如果你在后面加一个感叹号，看起来会更有精神！明天我打算尝试加两个感叹号。",
                "pen_name": "水稿大王"
            },
            # 投给感性派 AI早报，但充满官腔和八股文
            {
                "newspaper": shoegaze,
                "section": shoegaze_section,
                "title": "关于全面落实早睡早起精神的指导意见",
                "content": "为了进一步提高个人生活质量，必须紧紧围绕“早睡早起”这个核心，全面加强夜间玩手机的监督管理。我们要统一思想，提高认识，深刻理解早睡的重要战略意义。",
                "pen_name": "街道办小张"
            },
            # 投给感性派 AI早报，但完全像个菜谱
            {
                "newspaper": shoegaze,
                "section": shoegaze_section,
                "title": "如何煮一碗好吃的泡面",
                "content": "水开之后，先把面饼放进去煮三分钟，然后捞出来。这步很关键！然后重新烧一锅水，水开后放调料包，再把面放进去煮一分钟。这样面才会劲道！",
                "pen_name": "深夜食堂"
            }
        ]

        for item in terrible_submissions:
            # 1. 正常插入投稿记录
            sub = Submission(
                newspaper_id=item["newspaper"].id,
                section_id=item["section"].id,
                title=item["title"],
                content=item["content"],
                pen_name=item["pen_name"],
                char_count=len(item["content"]),
                status="pending"
            )
            db.add(sub)
            db.commit()
            db.refresh(sub)
            
            print(f"创建投稿 ID: {sub.id} -> 标题: {sub.title}")
            
            # 2. 同步调用 review 任务（阻塞等待 AI 回复，方便直接看到结果）
            # 由于在脚本中直接调用 .apply() 或 直接作为普通函数调用，就不会进 Celery 队列，而是直接执行！
            print(f"  正在触发 AI 审稿...")
            review_submission(sub.id)
            print(f"  AI 审稿完成！")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    trigger_real_ai_rejections()