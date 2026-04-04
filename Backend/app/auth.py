import datetime
import random
import string
import uuid

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.mail_service import send_otp_email
from app.max_bridge import validate_init_data
from app.models import OtpCode, RevokedToken, User

router = APIRouter(prefix="/auth", tags=["auth"])


# --- Схемы ---

class RequestOtpBody(BaseModel):
    email: EmailStr


class VerifyOtpBody(BaseModel):
    email: EmailStr
    code: str


class MaxAuthBody(BaseModel):
    init_data: str


# --- Утилиты ---

def generate_otp() -> str:
    return "".join(random.choices(string.digits, k=settings.OTP_LENGTH))


def create_jwt(user_id: int, email: str, role: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "jti": uuid.uuid4().hex,
        "exp": datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def decode_jwt(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Токен истёк")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Невалидный токен")


async def check_revoked(jti: str, db: AsyncSession):
    result = await db.execute(select(RevokedToken).where(RevokedToken.jti == jti))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=401, detail="Сессия завершена")


async def get_current_user(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Dependency — возвращает payload текущего пользователя из JWT."""
    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_jwt(token)
    await check_revoked(payload["jti"], db)
    return payload


def require_staff(user: dict = Depends(get_current_user)) -> dict:
    """Dependency — проверяет что пользователь staff."""
    if user.get("role") != "staff":
        raise HTTPException(status_code=403, detail="Доступ только для сотрудников")
    return user


# --- Эндпоинты ---

@router.post("/request-otp")
async def request_otp(body: RequestOtpBody, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user:
        user = User(email=body.email, role="staff")
        db.add(user)
        await db.flush()

    code = generate_otp()
    otp = OtpCode(
        user_id=user.id,
        code=code,
        expires_at=datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(seconds=settings.OTP_EXPIRE_SECONDS),
    )
    db.add(otp)
    await db.commit()

    await send_otp_email(body.email, code)

    return {"status": "ok", "message": "Код отправлен на почту"}


@router.post("/verify-otp")
async def verify_otp(body: VerifyOtpBody, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    now = datetime.datetime.now(datetime.timezone.utc)
    result = await db.execute(
        select(OtpCode)
        .where(
            OtpCode.user_id == user.id,
            OtpCode.code == body.code,
            OtpCode.is_used == False,
            OtpCode.expires_at > now,
        )
        .order_by(OtpCode.created_at.desc())
        .limit(1)
    )
    otp = result.scalar_one_or_none()

    if not otp:
        raise HTTPException(status_code=400, detail="Неверный или просроченный код")

    otp.is_used = True
    await db.commit()

    token = create_jwt(user.id, user.email, user.role)

    return {"status": "ok", "token": token, "role": user.role}


@router.post("/max")
async def max_auth(body: MaxAuthBody, db: AsyncSession = Depends(get_db)):
    """Авторизация через MAX Bridge initData."""
    data = validate_init_data(body.init_data)
    if not data:
        raise HTTPException(status_code=401, detail="Невалидные данные MAX Bridge")

    max_user = data.get("user")
    if not max_user:
        raise HTTPException(status_code=400, detail="Данные пользователя отсутствуют")

    max_user_id = max_user.get("id")
    first_name = max_user.get("first_name", "")
    username = max_user.get("username", "")

    # Email из MAX — формируем уникальный идентификатор
    max_email = f"max_{max_user_id}@max.local"

    result = await db.execute(select(User).where(User.email == max_email))
    user = result.scalar_one_or_none()

    if not user:
        user = User(email=max_email, role="staff")
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = create_jwt(user.id, max_email, user.role)

    return {
        "status": "ok",
        "token": token,
        "role": user.role,
        "user": {
            "id": user.id,
            "max_id": max_user_id,
            "first_name": first_name,
            "username": username,
        },
    }


@router.post("/guest")
async def guest_login(body: MaxAuthBody, db: AsyncSession = Depends(get_db)):
    """Гостевой вход — только из мини-приложения MAX."""
    data = validate_init_data(body.init_data)
    if not data:
        raise HTTPException(status_code=401, detail="Невалидные данные MAX Bridge")

    max_user = data.get("user", {})
    max_user_id = max_user.get("id")

    if not max_user_id:
        raise HTTPException(status_code=400, detail="Данные пользователя отсутствуют")

    guest_email = f"guest_max_{max_user_id}@max.local"

    result = await db.execute(select(User).where(User.email == guest_email))
    user = result.scalar_one_or_none()

    if not user:
        user = User(email=guest_email, role="guest")
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = create_jwt(user.id, guest_email, "guest")

    return {"status": "ok", "token": token, "role": "guest"}


@router.post("/refresh")
async def refresh_token(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_jwt(token)

    await check_revoked(payload["jti"], db)

    # Отозвать старый токен
    db.add(RevokedToken(jti=payload["jti"]))
    await db.commit()

    new_token = create_jwt(payload["sub"], payload["email"], payload.get("role", "guest"))

    return {"status": "ok", "token": new_token}


@router.post("/logout")
async def logout(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_jwt(token)

    await check_revoked(payload["jti"], db)

    db.add(RevokedToken(jti=payload["jti"]))
    await db.commit()

    return {"status": "ok", "message": "Сессия завершена"}
