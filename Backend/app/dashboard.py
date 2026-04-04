"""API эндпоинты для дашборда: топ-10 проблем и детальный просмотр."""
import datetime
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import Message, Source, Topic
from app.pdf_report import generate_topic_pdf

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

PERIOD_DAYS = {
    "today": 1,
    "week": 7,
    "month": 30,
}


@router.get("/topics")
async def get_topics(
    period: Optional[str] = Query(None, description="today, week, month"),
    industry: Optional[str] = Query(None, description="Фильтр по отрасли"),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Топ-10 проблем региона для дашборда."""
    query = select(Topic)

    # Фильтр по периоду
    if period and period in PERIOD_DAYS:
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=PERIOD_DAYS[period])
        query = query.where(Topic.last_seen_at >= cutoff)

    # Фильтр по отрасли
    if industry:
        query = query.where(Topic.category == industry)

    result = await db.execute(query.order_by(Topic.rank_score.desc()).limit(10))
    topics = result.scalars().all()

    return [
        {
            "key": t.id,
            "rank": i + 1,
            "title": t.title,
            "industry": t.category,
            "location": _location(t),
            "dynamic": t.trend_direction,
            "mentions": t.mentions_count,
        }
        for i, t in enumerate(topics)
    ]


@router.get("/topics/{topic_id}")
async def get_topic_detail(
    topic_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Детальная карточка проблемы."""
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalar_one_or_none()

    if not topic:
        raise HTTPException(status_code=404, detail="Тема не найдена")

    # Получить rank
    all_topics = await db.execute(select(Topic).order_by(Topic.rank_score.desc()))
    ranked = all_topics.scalars().all()
    rank = next((i + 1 for i, t in enumerate(ranked) if t.id == topic_id), 0)

    # Получить источники (сообщения)
    source_ids = []
    if topic.source_ids:
        try:
            source_ids = json.loads(topic.source_ids)
        except Exception:
            pass

    sources_list = []
    if source_ids:
        msg_ids = [int(sid) for sid in source_ids if str(sid).isdigit()]
        if msg_ids:
            result = await db.execute(
                select(Message, Source)
                .join(Source, Message.source_id == Source.id)
                .where(Message.id.in_(msg_ids))
                .order_by(Message.published_at.desc())
                .limit(20)
            )
            for msg, src in result.all():
                platform_tag = "TG" if src.platform == "telegram" else "MAX" if src.platform == "max" else "RSS"
                sources_list.append({
                    "platform": platform_tag,
                    "channel": src.name,
                    "message": msg.text[:200],
                    "date": msg.published_at.strftime("%d.%m.%Y") if msg.published_at else "",
                    "link": src.source_url or "#",
                })

    # Trend chart data
    chart_data = []
    if topic.trend_data:
        try:
            chart_data = json.loads(topic.trend_data)
        except Exception:
            pass

    # Keywords
    keywords = []
    if topic.keywords:
        try:
            keywords = json.loads(topic.keywords)
        except Exception:
            pass

    # Период
    period = ""
    if topic.first_seen_at and topic.last_seen_at:
        period = f"{topic.first_seen_at.strftime('%d %B')} — {topic.last_seen_at.strftime('%d %B %Y')}"

    return {
        "id": topic.id,
        "rank": rank,
        "title": topic.title,
        "industry": topic.category,
        "location": _location(topic),
        "period": period,
        "summary": topic.summary or "",
        "stats": {
            "mentionsGrowth": f"{topic.mentions_count} упоминаний",
            "locations": _count_locations(topic),
            "negativePct": round(topic.negative_ratio * 100),
        },
        "chartData": [
            {"day": p.get("date", ""), "mentions": p.get("mentions", 0)}
            for p in chart_data
        ],
        "peakLabel": f"Пик: {topic.peak_mentions} упоминаний" if topic.peak_mentions else "",
        "reliability": {
            "status": "confirmed" if len(sources_list) >= 2 else "suspicious" if len(sources_list) == 1 else "unclear",
            "confirmedSources": len(sources_list),
            "filteredBots": 0,
        },
        "sources": sources_list,
        "keywords": keywords,
        "dynamic": topic.trend_direction,
        "mentions": topic.mentions_count,
    }


@router.get("/topics/{topic_id}/pdf")
async def get_topic_pdf(
    topic_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Скачать PDF-отчёт по теме."""
    # Получить данные темы (тот же формат что и get_topic_detail)
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Тема не найдена")

    all_topics = await db.execute(select(Topic).order_by(Topic.rank_score.desc()))
    ranked = all_topics.scalars().all()
    rank = next((i + 1 for i, t in enumerate(ranked) if t.id == topic_id), 0)

    source_ids = []
    if topic.source_ids:
        try:
            source_ids = json.loads(topic.source_ids)
        except Exception:
            pass

    sources_list = []
    if source_ids:
        msg_ids = [int(sid) for sid in source_ids if str(sid).isdigit()]
        if msg_ids:
            result = await db.execute(
                select(Message, Source)
                .join(Source, Message.source_id == Source.id)
                .where(Message.id.in_(msg_ids))
                .order_by(Message.published_at.desc())
                .limit(20)
            )
            for msg, src in result.all():
                platform_tag = "TG" if src.platform == "telegram" else "MAX" if src.platform == "max" else "RSS"
                sources_list.append({
                    "platform": platform_tag,
                    "channel": src.name,
                    "message": msg.text[:200],
                    "date": msg.published_at.strftime("%d.%m.%Y") if msg.published_at else "",
                    "link": src.source_url or "",
                })

    keywords = []
    if topic.keywords:
        try:
            keywords = json.loads(topic.keywords)
        except Exception:
            pass

    period = ""
    if topic.first_seen_at and topic.last_seen_at:
        period = f"{topic.first_seen_at.strftime('%d.%m.%Y')} — {topic.last_seen_at.strftime('%d.%m.%Y')}"

    data = {
        "rank": rank,
        "title": topic.title,
        "industry": topic.category,
        "location": _location(topic),
        "period": period,
        "summary": topic.summary or "",
        "stats": {
            "mentionsGrowth": f"{topic.mentions_count} упоминаний",
            "locations": _count_locations(topic),
            "negativePct": round(topic.negative_ratio * 100),
        },
        "keywords": keywords,
        "reliability": {
            "status": "confirmed" if len(sources_list) >= 2 else "suspicious" if len(sources_list) == 1 else "unclear",
            "confirmedSources": len(sources_list),
            "filteredBots": 0,
        },
        "sources": sources_list,
    }

    pdf_bytes = generate_topic_pdf(data)

    filename = f"report_topic_{topic_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/topics/{topic_id}/send-pdf")
async def send_topic_pdf(
    topic_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Отправить PDF-отчёт пользователю через бота MAX."""
    import httpx as _httpx

    # Сгенерировать PDF (тот же код что и get_topic_pdf)
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Тема не найдена")

    all_topics = await db.execute(select(Topic).order_by(Topic.rank_score.desc()))
    ranked = all_topics.scalars().all()
    rank = next((i + 1 for i, t in enumerate(ranked) if t.id == topic_id), 0)

    source_ids = []
    if topic.source_ids:
        try:
            source_ids = json.loads(topic.source_ids)
        except Exception:
            pass

    sources_list = []
    if source_ids:
        msg_ids = [int(sid) for sid in source_ids if str(sid).isdigit()]
        if msg_ids:
            result = await db.execute(
                select(Message, Source)
                .join(Source, Message.source_id == Source.id)
                .where(Message.id.in_(msg_ids))
                .order_by(Message.published_at.desc())
                .limit(20)
            )
            for msg, src in result.all():
                platform_tag = "TG" if src.platform == "telegram" else "MAX" if src.platform == "max" else "RSS"
                sources_list.append({
                    "platform": platform_tag,
                    "channel": src.name,
                    "message": msg.text[:200],
                    "date": msg.published_at.strftime("%d.%m.%Y") if msg.published_at else "",
                })

    keywords = []
    if topic.keywords:
        try:
            keywords = json.loads(topic.keywords)
        except Exception:
            pass

    period = ""
    if topic.first_seen_at and topic.last_seen_at:
        period = f"{topic.first_seen_at.strftime('%d.%m.%Y')} — {topic.last_seen_at.strftime('%d.%m.%Y')}"

    data = {
        "rank": rank,
        "title": topic.title,
        "industry": topic.category,
        "location": _location(topic),
        "period": period,
        "summary": topic.summary or "",
        "stats": {
            "mentionsGrowth": f"{topic.mentions_count} упоминаний",
            "locations": _count_locations(topic),
            "negativePct": round(topic.negative_ratio * 100),
        },
        "keywords": keywords,
        "reliability": {
            "status": "confirmed" if len(sources_list) >= 2 else "suspicious" if len(sources_list) == 1 else "unclear",
            "confirmedSources": len(sources_list),
            "filteredBots": 0,
        },
        "sources": sources_list,
    }

    pdf_bytes = generate_topic_pdf(data)

    # Определить через какого бота отправить
    user_email = user.get("email", "")
    from app.config import settings

    # Отправить через MAX бот
    try:
        if "@max.local" in user_email:
            # Форматы: max_12345@max.local или guest_max_12345@max.local
            uid_part = user_email.split("@")[0]  # max_12345 или guest_max_12345
            # Извлекаем последнее число
            digits = "".join(c for c in uid_part.split("_")[-1] if c.isdigit())
            if not digits:
                raise HTTPException(status_code=400, detail="Не удалось определить MAX user ID")
            max_user_id = int(digits)
            from app.main import api
            import logging
            _logger = logging.getLogger(__name__)

            # 1. Получить URL для загрузки
            async with _httpx.AsyncClient() as client:
                upload_resp = await client.post(
                    "https://platform-api.max.ru/uploads",
                    params={"type": "file"},
                    headers={"Authorization": settings.MAX_BOT_TOKEN},
                )
                upload_resp.raise_for_status()
                upload_data = upload_resp.json()
                upload_url = upload_data.get("url")
                _logger.info("[PDF] Upload URL получен: %s", upload_url[:50])

                # 2. Загрузить PDF файл
                file_resp = await client.post(
                    upload_url,
                    files={"data": (f"report_{topic_id}.pdf", pdf_bytes, "application/pdf")},
                )
                _logger.info("[PDF] Файл загружен: %s | %s", file_resp.status_code, file_resp.text[:200])

                # token может быть в ответе uploads или в ответе загрузки
                file_token = None
                try:
                    file_data = file_resp.json()
                    file_token = file_data.get("token") or file_data.get("fileId")
                except Exception:
                    pass
                if not file_token:
                    file_token = upload_data.get("token") or upload_data.get("fileId")

                if file_token:
                    # 3. Подождать обработку файла на сервере MAX
                    import asyncio as _asyncio
                    await _asyncio.sleep(3)

                    # 4. Отправить сообщение с файлом
                    send_resp = await client.post(
                        "https://platform-api.max.ru/messages",
                        params={"user_id": max_user_id},
                        headers={
                            "Authorization": settings.MAX_BOT_TOKEN,
                            "Content-Type": "application/json",
                        },
                        json={
                            "text": f"PDF-отчёт: {topic.title}",
                            "attachments": [
                                {"type": "file", "payload": {"token": file_token}}
                            ],
                        },
                    )
                    _logger.info("[PDF] Отправка: %s | %s", send_resp.status_code, send_resp.text[:200])
                    if send_resp.status_code == 200:
                        return {"status": "ok", "method": "max", "message": "Отчёт отправлен в MAX"}
                else:
                    _logger.error("[PDF] Не удалось получить token файла")
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("[PDF] Ошибка отправки: %s", e)

    # Fallback — вернуть PDF для скачивания
    filename = f"report_topic_{topic_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/stats")
async def get_stats(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Общая статистика для дашборда."""
    from sqlalchemy import func as sa_func

    topics_count = await db.execute(select(sa_func.count(Topic.id)))
    messages_count = await db.execute(select(sa_func.count(Message.id)))
    sources_count = await db.execute(
        select(sa_func.count(Source.id)).where(Source.status == "approved")
    )

    return {
        "topics_count": topics_count.scalar() or 0,
        "messages_count": messages_count.scalar() or 0,
        "sources_count": sources_count.scalar() or 0,
    }


def _location(topic: Topic) -> str:
    parts = [topic.district, topic.city, topic.region]
    return next((p for p in parts if p), "Не определено")


def _count_locations(topic: Topic) -> int:
    count = 0
    if topic.region:
        count += 1
    if topic.city:
        count += 1
    if topic.district:
        count += 1
    return max(count, 1)
