"""
JWT 认证 — 登录态校验

- 登录接口返回 access_token
- 需鉴权接口通过 Authorization: Bearer <token> 获取当前用户
- 简单密码：盐 + SHA256，无额外依赖
"""

import hashlib
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models import User

_security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """简单盐哈希，与 JWT 共用密钥"""
    s = (settings.JWT_SECRET + password).encode("utf-8")
    return hashlib.sha256(s).hexdigest()


def verify_password(password: str, stored_hash: Optional[str]) -> bool:
    if not stored_hash:
        return False
    return hash_password(password) == stored_hash


def create_access_token(user_id: int) -> str:
    """生成 JWT access token"""
    import time
    payload = {"sub": str(user_id), "exp": int(time.time()) + settings.JWT_EXPIRE_MINUTES * 60}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def _decode_token(token: str) -> Optional[int]:
    """解析 token，返回 user_id 或 None"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return int(payload.get("sub", 0))
    except (jwt.InvalidTokenError, ValueError):
        return None


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    可选鉴权：有有效 token 则返回 User，否则返回 None。
    用于投稿等「登录则关联用户，未登录则匿名」的场景。
    """
    if not credentials or not credentials.credentials:
        return None
    user_id = _decode_token(credentials.credentials)
    if not user_id:
        return None
    user = db.query(User).filter(User.id == user_id).first()
    return user


async def get_current_user_required(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_security),
    db: Session = Depends(get_db),
) -> User:
    """
    必须鉴权：无有效 token 则 401。
    用于 /submissions/me 等必须登录的接口。
    """
    user = await get_current_user_optional(credentials, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
