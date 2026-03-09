from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "silicon_press",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.review_tasks",
        "app.tasks.curation_tasks",
        "app.tasks.publish_tasks",
        "app.tasks.mail_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
)

# 兜底自动发现，避免 worker 启动时遗漏任务模块导致 unregistered task
celery_app.autodiscover_tasks(["app.tasks"])

# ── 定时任务调度 ──
celery_app.conf.beat_schedule = {
    # 每日 23:00 UTC+8 — 选稿 + 编辑
    "curate-daily-articles": {
        "task": "app.tasks.curation_tasks.curate_daily_articles",
        "schedule": crontab(hour=23, minute=0),
        "options": {"expires": 3600},
    },

    # 每日 06:30 UTC+8 — 排版
    "generate-daily-layout": {
        "task": "app.tasks.publish_tasks.generate_layout",
        "schedule": crontab(hour=6, minute=30),
        "options": {"expires": 3600},
    },

    # 每日 07:00 UTC+8 — 发布
    "publish-daily-issue": {
        "task": "app.tasks.publish_tasks.publish_issue",
        "schedule": crontab(hour=7, minute=0),
        "options": {"expires": 3600},
    },
}
