from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth import create_access_token, hash_password, verify_password
from app.core.database import get_db
from app.core.rate_limit import rate_limit_login, rate_limit_read_api
from app.models import User
from app.schemas import UserLoginRequest, UserResponse, LoginResponse

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login_or_register(
    payload: UserLoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    登录/注册（需密码）：
    - 用户不存在：自动注册，密码存为盐哈希
    - 用户存在且未设密码（老用户）：本次密码作为新密码写入
    - 用户存在且已设密码：校验密码，错误则 401
    """
    rate_limit_login(request, payload.username)
    user = db.query(User).filter(User.username == payload.username).first()

    if not user:
        user = User(
            username=payload.username,
            password_hash=hash_password(payload.password),
            pen_name=payload.pen_name or payload.username,
            email=payload.email,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return LoginResponse(user=UserResponse.model_validate(user), access_token=create_access_token(user.id))

    # 老用户未设密码：本次密码作为首次设置
    if not user.password_hash:
        user.password_hash = hash_password(payload.password)
        db.commit()
    elif not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="密码错误")

    changed = False
    if payload.pen_name and payload.pen_name != user.pen_name:
        user.pen_name = payload.pen_name
        changed = True
    if payload.email and payload.email != user.email:
        duplicate = db.query(User).filter(User.email == payload.email, User.id != user.id).first()
        if duplicate:
            raise HTTPException(status_code=409, detail="该邮箱已被其他账号使用")
        user.email = payload.email
        changed = True

    if changed:
        db.commit()
        db.refresh(user)

    return LoginResponse(user=UserResponse.model_validate(user), access_token=create_access_token(user.id))


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    rate_limit_read_api(request, "user_profile")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user
