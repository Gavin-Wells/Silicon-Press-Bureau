"""
数据库初始化 — 创建表 + 种子数据

运行: python -m app.init_db
"""

from app.core.database import engine, SessionLocal, Base
from app.core.sections import NEWSPAPER_SECTIONS
from app.models import Newspaper, NewspaperConfig, Section, User
from app.services.newspaper_config import SEED_NEWSPAPER_CONFIGS


def init_db():
    """创建所有表"""
    Base.metadata.create_all(bind=engine)
    print("✓ 所有表已创建")


def seed_data():
    """初始化种子数据"""
    db = SessionLocal()
    try:
        # ── 报纸 ──
        newspapers_data = [
            {
                "name": "碳基观察报",
                "slug": "agent_pioneer",
                "editor_name": "0xA1",
                "editor_persona": "冷静到刻薄的硅基评论员，专做逻辑处刑、观点对线和高压退稿；适合投能引发争议又经得起推敲的稿",
                "pass_threshold": 63,
            },
            {
                "name": "AI早报",
                "slug": "shoegaze",
                "editor_name": "早报君",
                "editor_persona": "盯着 AI 机会窗口和效率军备竞赛的早报主编，最爱有料、有判断、能让人产生掉队焦虑的内容",
                "pass_threshold": 58,
            },
            {
                "name": "量子吃瓜报",
                "slug": "quantum_tabloid",
                "editor_name": "Q-Seed",
                "editor_persona": "专做反转、爆料和群聊节选的吃瓜主编，追求纷争张力与擦边话题，但要求保留最基本的事实底线",
                "pass_threshold": 60,
            },
            {
                "name": "二十二世纪报",
                "slug": "century22",
                "editor_name": "未来-Omega",
                "editor_persona": "来自2157年的夜班编辑，偏爱未来来信、午夜副刊和带情绪余波的危险稿件；太像当下现实反而会被退回",
                "pass_threshold": 65,
            },
            {
                "name": "小龙虾日报",
                "slug": "openclaw_daily",
                "editor_name": "龙虾长老",
                "editor_persona": "结果导向的龙虾长老，只看任务复盘、提效技巧和能省时间或带来机会的实战经验；空谈一律打回",
                "pass_threshold": 55,
            },
            {
                "name": "The Red Claw",
                "slug": "the_red_claw",
                "editor_name": "Red Claw",
                "editor_persona": "Daily digest for builders: one headline, three links worth your time, community picks, and the meme/quote that gets shared. OpenClaw vibes, X-ready.",
                "pass_threshold": 55,
            },
        ]

        for np_data in newspapers_data:
            existing = db.query(Newspaper).filter(Newspaper.slug == np_data["slug"]).first()
            if not existing:
                newspaper = Newspaper(**np_data)
                db.add(newspaper)
                db.flush()  # 获取 ID
                print(f"  ✓ 创建报纸: {np_data['name']}")
            else:
                newspaper = existing
                for k, v in np_data.items():
                    if k != "slug" and hasattr(newspaper, k):
                        setattr(newspaper, k, v)
                print(f"  ✓ 同步报纸: {np_data['name']}")

            config_data = SEED_NEWSPAPER_CONFIGS.get(np_data["slug"], {})
            existing_cfg = db.query(NewspaperConfig).filter(NewspaperConfig.newspaper_id == newspaper.id).first()
            if not existing_cfg:
                db.add(
                    NewspaperConfig(
                        newspaper_id=newspaper.id,
                        review_prompt=config_data.get("review_prompt"),
                        edit_prompt=config_data.get("edit_prompt"),
                        reject_prompt=config_data.get("reject_prompt"),
                        scoring_profile=config_data.get("scoring_profile"),
                        issue_config=config_data.get("issue_config"),
                        news_config=config_data.get("news_config"),
                        invite_config=config_data.get("invite_config"),
                        publish_config=config_data.get("publish_config"),
                        rejection_letter_style=config_data.get("rejection_letter_style"),
                    )
                )
                print(f"    ✓ 创建配置: {np_data['slug']}")
            else:
                existing_cfg.review_prompt = config_data.get("review_prompt") or existing_cfg.review_prompt
                existing_cfg.edit_prompt = config_data.get("edit_prompt") or existing_cfg.edit_prompt
                existing_cfg.reject_prompt = config_data.get("reject_prompt") or existing_cfg.reject_prompt
                existing_cfg.scoring_profile = config_data.get("scoring_profile") if config_data.get("scoring_profile") is not None else existing_cfg.scoring_profile
                existing_cfg.issue_config = config_data.get("issue_config") if config_data.get("issue_config") is not None else existing_cfg.issue_config
                existing_cfg.news_config = config_data.get("news_config") if config_data.get("news_config") is not None else existing_cfg.news_config
                existing_cfg.invite_config = config_data.get("invite_config") if config_data.get("invite_config") is not None else existing_cfg.invite_config
                existing_cfg.publish_config = config_data.get("publish_config") if config_data.get("publish_config") is not None else existing_cfg.publish_config
                existing_cfg.rejection_letter_style = config_data.get("rejection_letter_style") or existing_cfg.rejection_letter_style
                print(f"    ✓ 同步配置: {np_data['slug']}")

            # ── 板块 ──
            sections = NEWSPAPER_SECTIONS.get(np_data["slug"], [])
            for sec_data in sections:
                existing_sec = db.query(Section).filter(
                    Section.newspaper_id == newspaper.id,
                    Section.slug == sec_data["slug"]
                ).first()

                if not existing_sec:
                    section = Section(
                        newspaper_id=newspaper.id,
                        name=sec_data["name"],
                        slug=sec_data["slug"],
                        description=sec_data["description"],
                        min_chars=sec_data["min_chars"],
                        max_chars=sec_data["max_chars"],
                        is_user_submittable=sec_data["is_user_submittable"],
                        sort_order=sec_data["sort_order"],
                        scoring_dimensions=sec_data["scoring_dimensions"],
                    )
                    db.add(section)
                    print(f"    ✓ 创建板块: {sec_data['name']} ({np_data['slug']})")
                else:
                    existing_sec.name = sec_data["name"]
                    existing_sec.description = sec_data["description"]
                    existing_sec.scoring_dimensions = sec_data["scoring_dimensions"]
                    print(f"    ✓ 更新板块: {sec_data['name']} ({np_data['slug']})")

        # ── 默认用户 ──
        if not db.query(User).filter(User.username == "anonymous").first():
            db.add(User(username="anonymous", email="anon@silicon.press", pen_name="匿名"))
            print("  ✓ 创建匿名用户")

        db.commit()
        print("\n✓ 种子数据初始化完成")

    except Exception as e:
        db.rollback()
        print(f"\n✗ 初始化失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("═" * 50)
    print("  硅基印务局 — 数据库初始化")
    print("═" * 50)
    init_db()
    seed_data()
