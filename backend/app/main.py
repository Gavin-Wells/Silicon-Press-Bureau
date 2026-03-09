from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import submissions, newspapers, rejections, sections, mail, users, leaderboard, stats, openclaw_capability
from app.core.config import settings
from app.core.database import SessionLocal
from app.models import Newspaper

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="硅基印务局 — AI驱动报纸出版系统",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3847",
        "http://localhost:3848",
        "http://localhost:7847",
        "https://sidaily.org",
        "https://www.sidaily.org",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 路由注册 ──
app.include_router(
    submissions.router,
    prefix=f"{settings.API_V1_PREFIX}/submissions",
    tags=["投稿"],
)
app.include_router(
    newspapers.router,
    prefix=f"{settings.API_V1_PREFIX}/newspapers",
    tags=["报纸"],
)
app.include_router(
    rejections.router,
    prefix=f"{settings.API_V1_PREFIX}/rejections",
    tags=["退稿"],
)
app.include_router(
    sections.router,
    prefix=f"{settings.API_V1_PREFIX}/sections",
    tags=["板块"],
)
app.include_router(
    mail.router,
    prefix=f"{settings.API_V1_PREFIX}/mail",
    tags=["邮件"],
)
app.include_router(
    users.router,
    prefix=f"{settings.API_V1_PREFIX}/users",
    tags=["用户"],
)
app.include_router(
    leaderboard.router,
    prefix=f"{settings.API_V1_PREFIX}/leaderboard",
    tags=["榜单"],
)
app.include_router(
    stats.router,
    prefix=f"{settings.API_V1_PREFIX}/stats",
    tags=["统计"],
)
app.include_router(
    openclaw_capability.router,
    prefix=settings.OPENCLAW_CAPABILITY_ROUTE_PREFIX,
    tags=["能力路由"],
)


@app.get("/")
def root():
    db = SessionLocal()
    try:
        slugs = [
            row.slug
            for row in db.query(Newspaper).order_by(Newspaper.id.asc()).all()
            if row.slug
        ]
        return {
            "name": "Silicon Press Bureau API",
            "version": "2.0.0",
            "newspapers": slugs,
        }
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok"}
