import hashlib
import time
import uuid
from typing import Optional

import redis
from fastapi import HTTPException, Request, Response

from app.core.config import settings

_redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


def get_client_ip(request: Request) -> str:
    """
    获取客户端 IP。仅当请求来自可信代理时信任 X-Forwarded-For，
    否则易被伪造绕过限流。
    """
    trusted = [ip.strip() for ip in settings.TRUSTED_PROXY_IPS.split(",") if ip.strip()]
    if trusted and request.client and request.client.host in trusted:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def ensure_anon_id(request: Request, response: Response) -> str:
    anon_id = request.cookies.get(settings.ANON_COOKIE_NAME)
    if anon_id:
        return anon_id

    anon_id = uuid.uuid4().hex
    response.set_cookie(
        key=settings.ANON_COOKIE_NAME,
        value=anon_id,
        max_age=settings.ANON_COOKIE_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
    )
    return anon_id


def _incr_with_expire(key: str, ttl_seconds: int) -> Optional[int]:
    try:
        current = _redis_client.incr(key)
        if current == 1:
            _redis_client.expire(key, ttl_seconds)
        return int(current)
    except redis.RedisError:
        if settings.RATE_LIMIT_FAIL_OPEN:
            # 可用性优先：Redis 异常时放行，避免误伤正常投稿
            return None
        # 安全优先：Redis 异常时拒绝匿名投稿请求
        raise HTTPException(status_code=503, detail="限流服务异常，请稍后再试")


def _check_limit(current: Optional[int], limit: int, message: str):
    if current is not None and current > limit:
        raise HTTPException(status_code=429, detail=message)


def _content_hash(title: str, content: str) -> str:
    text = f"{title.strip().lower()}::{content.strip().lower()}"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def enforce_anonymous_submission_guard(anon_id: str, client_ip: str, title: str, content: str):
    now = int(time.time())
    minute_bucket = now // 60
    hour_bucket = now // 3600

    anon_minute_key = f"rate:anon:{anon_id}:m:{minute_bucket}"
    anon_hour_key = f"rate:anon:{anon_id}:h:{hour_bucket}"
    ip_minute_key = f"rate:ip:{client_ip}:m:{minute_bucket}"
    ip_hour_key = f"rate:ip:{client_ip}:h:{hour_bucket}"

    anon_minute_count = _incr_with_expire(anon_minute_key, 120)
    anon_hour_count = _incr_with_expire(anon_hour_key, 7200)
    ip_minute_count = _incr_with_expire(ip_minute_key, 120)
    ip_hour_count = _incr_with_expire(ip_hour_key, 7200)

    _check_limit(
        anon_minute_count,
        settings.ANON_SUBMIT_LIMIT_PER_MINUTE,
        f"提交过于频繁，请稍后再试（匿名用户每分钟最多提交 {settings.ANON_SUBMIT_LIMIT_PER_MINUTE} 次）",
    )
    _check_limit(
        anon_hour_count,
        settings.ANON_SUBMIT_LIMIT_PER_HOUR,
        f"提交过于频繁，请稍后再试（匿名用户每小时最多提交 {settings.ANON_SUBMIT_LIMIT_PER_HOUR} 次）",
    )
    _check_limit(
        ip_minute_count,
        settings.ANON_IP_LIMIT_PER_MINUTE,
        "该网络环境提交过于频繁，请稍后再试",
    )
    _check_limit(
        ip_hour_count,
        settings.ANON_IP_LIMIT_PER_HOUR,
        "该网络环境本小时提交过于频繁，请稍后再试",
    )

    # 内容去重：10 分钟内同样的标题+正文只允许提交一次
    dedupe_key = f"dedupe:submission:{_content_hash(title, content)}"
    try:
        inserted = _redis_client.set(dedupe_key, "1", nx=True, ex=settings.ANON_DEDUP_TTL_SECONDS)
    except redis.RedisError:
        if settings.RATE_LIMIT_FAIL_OPEN:
            inserted = True
        else:
            raise HTTPException(status_code=503, detail="限流服务异常，请稍后再试")

    if not inserted:
        raise HTTPException(status_code=429, detail="检测到重复投稿，请勿重复提交")
