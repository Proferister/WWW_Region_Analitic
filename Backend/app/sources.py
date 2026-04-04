from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import delete as sa_delete

from app.auth import get_current_user, require_staff
from app.database import get_db
from app.models import Message, Source
from app.rss_parser import validate_feed

router = APIRouter(prefix="/sources", tags=["sources"])

ALLOWED_PLATFORMS = {"max", "telegram", "vk", "rss"}


# --- Схемы ---

class SourceCreate(BaseModel):
    platform: str  # "max", "telegram", "vk"
    name: str
    description: str | None = None
    source_id: str
    source_url: str | None = None


class SourceUpdate(BaseModel):
    is_active: bool | None = None
    name: str | None = None
    description: str | None = None
    trust_score: int | None = None  # 0-100


class RssSourceCreate(BaseModel):
    url: str  # Ссылка на RSS/ATOM фид


# --- Эндпоинты ---

@router.post("/rss", status_code=201)
async def create_rss_source(
    body: RssSourceCreate,
    user: dict = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """Добавить RSS/ATOM источник по URL. Парсит название и иконку автоматически."""
    feed = await validate_feed(body.url)
    if not feed:
        raise HTTPException(status_code=400, detail="Не удалось найти RSS/ATOM фид по указанной ссылке")

    # Проверить дубликат
    result = await db.execute(
        select(Source).where(Source.source_id == body.url, Source.platform == "rss")
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Этот RSS-источник уже добавлен")

    source = Source(
        user_id=int(user["sub"]),
        platform="rss",
        name=feed["title"],
        description=feed["description"],
        source_id=body.url,
        source_url=feed["link"],
        avatar_url=feed["favicon_url"],
        status="approved",
        is_active=True,
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)

    return {
        "id": source.id,
        "platform": source.platform,
        "name": source.name,
        "description": source.description,
        "source_id": source.source_id,
        "source_url": source.source_url,
        "avatar_url": source.avatar_url,
        "status": source.status,
        "is_active": source.is_active,
        "trust_score": source.trust_score,
        "created_at": source.created_at.isoformat(),
    }


@router.get("")
async def list_sources(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Список всех источников. Доступно staff и guest."""
    result = await db.execute(select(Source).order_by(Source.created_at.desc()))
    sources = result.scalars().all()
    return [
        {
            "id": s.id,
            "platform": s.platform,
            "name": s.name,
            "description": s.description,
            "source_id": s.source_id,
            "source_url": s.source_url,
            "avatar_url": s.avatar_url,
            "status": s.status,
            "is_active": s.is_active,
            "trust_score": s.trust_score,
            "created_at": s.created_at.isoformat(),
        }
        for s in sources
    ]


@router.get("/pending")
async def list_pending_sources(
    user: dict = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """Список источников, ожидающих подтверждения. Только staff."""
    result = await db.execute(
        select(Source).where(Source.status == "pending").order_by(Source.created_at.desc())
    )
    sources = result.scalars().all()
    return [
        {
            "id": s.id,
            "platform": s.platform,
            "name": s.name,
            "description": s.description,
            "source_id": s.source_id,
            "source_url": s.source_url,
            "avatar_url": s.avatar_url,
            "status": s.status,
            "is_active": s.is_active,
            "trust_score": s.trust_score,
            "created_at": s.created_at.isoformat(),
        }
        for s in sources
    ]


@router.post("", status_code=201)
async def create_source(
    body: SourceCreate,
    user: dict = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """Добавить источник. Только staff."""
    if body.platform not in ALLOWED_PLATFORMS:
        raise HTTPException(
            status_code=400,
            detail=f"Платформа должна быть одной из: {', '.join(ALLOWED_PLATFORMS)}",
        )

    source = Source(
        user_id=user["sub"],
        platform=body.platform,
        name=body.name,
        description=body.description,
        source_id=body.source_id,
        source_url=body.source_url,
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)

    return {
        "id": source.id,
        "platform": source.platform,
        "name": source.name,
        "description": source.description,
        "source_id": source.source_id,
        "source_url": source.source_url,
        "avatar_url": source.avatar_url,
        "status": source.status,
        "is_active": source.is_active,
        "trust_score": source.trust_score,
        "created_at": source.created_at.isoformat(),
    }


@router.patch("/{source_id}")
async def update_source(
    source_id: int,
    body: SourceUpdate,
    user: dict = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """Обновить источник (вкл/выкл, название, описание). Только staff."""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Источник не найден")

    if body.is_active is not None:
        source.is_active = body.is_active
    if body.name is not None:
        source.name = body.name
    if body.description is not None:
        source.description = body.description
    if body.trust_score is not None:
        source.trust_score = max(0, min(100, body.trust_score))

    await db.commit()

    return {
        "id": source.id,
        "platform": source.platform,
        "name": source.name,
        "description": source.description,
        "source_id": source.source_id,
        "source_url": source.source_url,
        "avatar_url": source.avatar_url,
        "status": source.status,
        "is_active": source.is_active,
        "trust_score": source.trust_score,
        "created_at": source.created_at.isoformat(),
    }


@router.post("/{source_id}/approve")
async def approve_source(
    source_id: int,
    user: dict = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """Подтвердить источник. Только staff."""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Источник не найден")

    source.status = "approved"
    source.is_active = True
    await db.commit()

    return {
        "id": source.id,
        "platform": source.platform,
        "name": source.name,
        "description": source.description,
        "source_id": source.source_id,
        "source_url": source.source_url,
        "avatar_url": source.avatar_url,
        "status": source.status,
        "is_active": source.is_active,
        "trust_score": source.trust_score,
        "created_at": source.created_at.isoformat(),
    }


@router.post("/{source_id}/reject")
async def reject_source(
    source_id: int,
    user: dict = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """Отклонить источник. Только staff. Бот покидает чат."""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Источник не найден")

    source.status = "rejected"
    source.is_active = False
    await db.commit()

    # Бот покидает чат
    await _leave_source_chat(source)

    return {"status": "ok", "message": f"Источник «{source.name}» отклонён"}


@router.delete("/{source_id}")
async def delete_source(
    source_id: int,
    user: dict = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """Удалить источник. Только staff. Бот покидает чат."""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Источник не найден")

    # Бот покидает чат (только MAX/Telegram, не RSS)
    await _leave_source_chat(source)

    # Удалить связанные сообщения
    await db.execute(sa_delete(Message).where(Message.source_id == source.id))
    await db.delete(source)
    await db.commit()

    return {"status": "ok", "message": "Источник удалён"}


async def _leave_source_chat(source: Source):
    """Бот покидает чат на соответствующей платформе."""
    try:
        chat_id = int(source.source_id)
        if source.platform == "max":
            from app.main import api
            await api.leave_chat(chat_id)
        elif source.platform == "telegram":
            from app.main import tg
            await tg.leave_chat(chat_id)
    except Exception:
        pass
