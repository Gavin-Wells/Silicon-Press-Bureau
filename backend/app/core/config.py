from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://silicon:CHANGE_ME@localhost:5847/silicon_press"
    REDIS_URL: str = "redis://localhost:6847"
    LLM_CONFIG_PATH: str = "llm.json"
    REVIEW_EDITOR_KEYS: str = ""
    REVIEW_LLM_MAX_WORKERS: int = 4
    INVITE_EDITOR_KEY: str = ""
    INVITE_NEWS_ENABLED: bool = True
    INVITE_NEWS_MAX_ITEMS: int = 8
    INVITE_NEWS_TIMEOUT_SECONDS: int = 8
    CURATION_LLM_MAX_WORKERS: int = 6
    LLM_TIMEOUT_SECONDS: int = 30
    CURATION_DAILY_LIMIT: int = 15
    CURATION_FRESH_WINDOW_HOURS: int = 24
    CURATION_FRESH_QUOTA_RATIO: float = 0.3
    CURATION_TIME_DECAY_PER_DAY: float = 2.0
    CURATION_ARCHIVE_AFTER_DAYS: int = 7
    # 每期至少邀稿篇数，保证版面有「时事/反差」味，即使真人稿已够也补
    CURATION_MIN_INVITE_PER_ISSUE: int = 2
    PREVIEW_ADMIN_USERS: str = ""

    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Silicon Press Bureau"
    OPENCLAW_CAPABILITY_ROUTE_PREFIX: str = "/api/v1/openclaw-capability"

    # JWT Auth
    JWT_SECRET: str = "change-me-jwt-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # 仅当请求来自可信代理时信任 X-Forwarded-For（逗号分隔 IP，如 "127.0.0.1,::1"）
    TRUSTED_PROXY_IPS: str = ""
    # HTTPS 环境下设为 True，cookie 仅通过加密连接传输
    COOKIE_SECURE: bool = False

    # Anonymous submission anti-spam
    ANON_COOKIE_NAME: str = "spb_anon_id"
    ANON_COOKIE_MAX_AGE_SECONDS: int = 60 * 60 * 24 * 365
    ANON_SUBMIT_LIMIT_PER_MINUTE: int = 1
    ANON_SUBMIT_LIMIT_PER_HOUR: int = 15
    ANON_IP_LIMIT_PER_MINUTE: int = 10
    ANON_IP_LIMIT_PER_HOUR: int = 120
    ANON_DEDUP_TTL_SECONDS: int = 60 * 10
    USER_SUBMIT_LIMIT_PER_MINUTE: int = 1
    USER_SUBMIT_LIMIT_PER_HOUR: int = 30

    # Endpoint rate limits
    LOGIN_IP_LIMIT_PER_MINUTE: int = 20
    LOGIN_USERNAME_LIMIT_PER_MINUTE: int = 8
    COMPARE_IP_LIMIT_PER_MINUTE: int = 3
    COMPARE_IP_LIMIT_PER_HOUR: int = 20
    COMPARE_USER_LIMIT_PER_MINUTE: int = 6
    COMPARE_USER_LIMIT_PER_HOUR: int = 40
    READ_API_IP_LIMIT_PER_MINUTE: int = 120
    # True: Redis 限流故障时放行；False: Redis 故障时拒绝请求（更安全）
    RATE_LIMIT_FAIL_OPEN: bool = True

    # Email Service Configuration
    MAIL_SERVER_IMAP: str = "imap.exmail.qq.com"
    MAIL_SERVER_IMAP_PORT: int = 993
    MAIL_SERVER_IMAP_SSL: bool = True

    MAIL_SERVER_SMTP: str = "smtp.exmail.qq.com"
    MAIL_SERVER_SMTP_PORT: int = 465
    MAIL_SERVER_SMTP_SSL: bool = True

    MAIL_ENABLED: bool = True
    MAIL_FROM_ADDRESS: str = ""
    MAIL_FROM_NAME: str = "Silicon Press Bureau"
    MAIL_TIMEOUT_SECONDS: int = 10

    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
