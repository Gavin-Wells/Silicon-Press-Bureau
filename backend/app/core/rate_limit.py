"""
Redis 限流 — 按 IP / 用户维度限制请求频率
"""

import time
from hashlib import sha256

import redis
from fastapi import HTTPException, Request

from app.core.config import settings
from app.services.anti_spam import get_client_ip

_redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


def _check(key: str, limit: int, window_seconds: int) -> None:
    """超过 limit 则抛 429"""
    try:
        now = int(time.time())
        bucket = now // window_seconds
        rkey = f"rate:{key}:{bucket}"
        n = _redis.incr(rkey)
        if n == 1:
            _redis.expire(rkey, window_seconds * 2)
        if n > limit:
            raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
    except redis.RedisError:
        if settings.RATE_LIMIT_FAIL_OPEN:
            return  # 可用性优先：降级放行
        raise HTTPException(status_code=503, detail="限流服务异常，请稍后再试")


def rate_limit_user_submit(user_id: int) -> None:
    """登录用户投稿限流：每用户每分钟/小时限制"""
    _check(f"user_submit:{user_id}:m", settings.USER_SUBMIT_LIMIT_PER_MINUTE, 60)
    _check(f"user_submit:{user_id}:h", settings.USER_SUBMIT_LIMIT_PER_HOUR, 3600)


def rate_limit_compare(request: Request, user_id: int | None = None) -> None:
    """高成本 compare 接口限流：IP 与用户双维度限制"""
    ip = get_client_ip(request)
    _check(f"compare:ip:{ip}:m", settings.COMPARE_IP_LIMIT_PER_MINUTE, 60)
    _check(f"compare:ip:{ip}:h", settings.COMPARE_IP_LIMIT_PER_HOUR, 3600)
    if user_id is not None:
        _check(f"compare:user:{user_id}:m", settings.COMPARE_USER_LIMIT_PER_MINUTE, 60)
        _check(f"compare:user:{user_id}:h", settings.COMPARE_USER_LIMIT_PER_HOUR, 3600)


def rate_limit_login(request: Request, username: str) -> None:
    """登录接口限流：IP + 用户名双维度"""
    ip = get_client_ip(request)
    username_key = sha256(username.strip().lower().encode("utf-8")).hexdigest()[:16]
    _check(f"login:ip:{ip}:m", settings.LOGIN_IP_LIMIT_PER_MINUTE, 60)
    _check(f"login:user:{username_key}:m", settings.LOGIN_USERNAME_LIMIT_PER_MINUTE, 60)


def rate_limit_read_api(request: Request, scope: str) -> None:
    """公开查询接口限流，降低枚举/爬取风险"""
    ip = get_client_ip(request)
    _check(f"read:{scope}:ip:{ip}:m", settings.READ_API_IP_LIMIT_PER_MINUTE, 60)
