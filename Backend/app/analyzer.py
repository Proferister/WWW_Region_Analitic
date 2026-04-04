"""Сервис анализа: очередь GigaChat (1 поток), только негативные, дедупликация, доверенность."""
import asyncio
import datetime
import json
import logging
import re

from sqlalchemy import select

from app.ai_analyze import (
    ProblemCardsBuildRequest,
    ProblemSourceInput,
    analyze_message_llm,
    build_problem_cards_llm,
)
from app.database import async_session
from app.models import Message, Source, Topic

logger = logging.getLogger(__name__)

# Очередь для GigaChat — один поток
_gigachat_queue: asyncio.Queue = asyncio.Queue()
_gigachat_lock = asyncio.Lock()


# ==================== ОЧЕРЕДЬ GIGACHAT ====================

async def gigachat_worker():
    """Воркер: берёт задачи из очереди и выполняет последовательно (1 поток)."""
    while True:
        task = await _gigachat_queue.get()
        try:
            await task
        except Exception as e:
            logger.error("[GigaChat Worker] Ошибка: %s", e)
        finally:
            _gigachat_queue.task_done()
            # Пауза между запросами чтобы не получить 429
            await asyncio.sleep(1)


# ==================== АНАЛИЗ СООБЩЕНИЙ ====================

async def analyze_loop():
    """Фоновый цикл: анализирует новые сообщения каждые 30 секунд."""
    while True:
        try:
            await _analyze_batch()
        except Exception as e:
            logger.error("[Analyzer] Ошибка: %s", e)
        await asyncio.sleep(30)


async def _analyze_batch():
    """Берёт неанализированные сообщения и ставит в очередь по одному."""
    async with async_session() as db:
        result = await db.execute(
            select(Message)
            .where(
                Message.is_analyzed == False,
                Message.is_duplicate == False,
            )
            .order_by(Message.collected_at)
            .limit(10)
        )
        messages = result.scalars().all()

    if not messages:
        return

    for msg in messages:
        # Каждое сообщение — отдельная задача в очереди
        await _gigachat_queue.put(_analyze_single(msg.id, msg.source_id, msg.text))


ROSTOV_MARKERS = [
    "ростов", "ростовск", "дон ", "донск", "на-дону", "на дону",
    "аксай", "азов", "батайск", "таганрог", "новочеркасск", "шахты", "волгодонск",
    "каменск", "сальск", "гуково", "донецк", "миллерово", "морозовск",
    "новошахтинск", "зверево", "семикаракорск", "цимлянск", "константиновск",
    "пролетарск", "багаевск", "белая калитва", "красный сулин",
    "аксайск", "азовск", "мясниковск", "матвеево-курган",
    "темерник", "суворовск", "левенцовк", "чалтырь",
    "ростовской области", "ростовская область",
]


def _is_rostov_related(text: str) -> bool:
    """Проверить что текст касается Ростовской области."""
    lower = text.lower()
    return any(marker in lower for marker in ROSTOV_MARKERS)


async def _analyze_single(msg_id: int, source_id: int, text: str):
    """Анализирует одно сообщение через GigaChat (вызывается из воркера)."""
    # Пропустить если не касается Ростовской области
    if not _is_rostov_related(text):
        async with async_session() as db:
            result = await db.execute(select(Message).where(Message.id == msg_id))
            m = result.scalar_one_or_none()
            if m:
                m.is_analyzed = True
                m.sentiment = "neutral"
                m.region = None
                await db.commit()
        logger.info("[Analyzer] #%d: пропущено — не Ростовская область", msg_id)
        return
    async with async_session() as db:
        src_result = await db.execute(select(Source).where(Source.id == source_id))
        source = src_result.scalar_one_or_none()

    channel_name = source.name if source else ""
    channel_desc = source.description or "" if source else ""

    try:
        async with _gigachat_lock:
            data = await analyze_message_llm(text, channel_name, channel_desc)

        region = data.get("region") or "Ростовская область"
        city = data.get("city")
        district = data.get("district")

        async with async_session() as db:
            result = await db.execute(select(Message).where(Message.id == msg_id))
            m = result.scalar_one_or_none()
            if m:
                m.is_analyzed = True
                m.category = data.get("category")
                m.sentiment = data.get("sentiment")
                m.region = region
                m.city = city
                m.district = district
                m.summary = data.get("short_summary")
                m.problem_signature = data.get("problem_signature")
                m.keywords = json.dumps(data.get("key_words", []), ensure_ascii=False)
                await db.commit()

        logger.info("[Analyzer] #%d: %s | %s | %s", msg_id, data.get("category"), data.get("sentiment"),
                    district or city or region)

    except Exception as e:
        error_detail = str(e)
        error_type = type(e).__name__
        # Подробная информация об ошибке GigaChat
        if hasattr(e, 'status_code'):
            logger.error("[Analyzer] GigaChat ошибка #%d | HTTP %s | %s: %s",
                         msg_id, getattr(e, 'status_code', '?'), error_type, error_detail)
        elif hasattr(e, 'response'):
            resp = getattr(e, 'response', None)
            status = resp.status_code if resp else '?'
            body = resp.text[:500] if resp else ''
            logger.error("[Analyzer] HTTP ошибка #%d | %s | %s | body: %s",
                         msg_id, status, error_detail, body)
        else:
            logger.error("[Analyzer] Ошибка #%d | %s: %s", msg_id, error_type, error_detail)

        async with async_session() as db:
            result = await db.execute(select(Message).where(Message.id == msg_id))
            m = result.scalar_one_or_none()
            if m:
                m.is_analyzed = True
                m.sentiment = "neutral"
                await db.commit()


# ==================== ПОСТРОЕНИЕ ТОПИКОВ ====================

async def build_topics_loop():
    """Фоновый цикл: пересобирает топики каждые 5 минут."""
    while True:
        try:
            await build_topics()
        except Exception as e:
            logger.error("[Topics] Ошибка: %s", e)
        await asyncio.sleep(300)


async def build_topics():
    """Строит топики: только негативные, без дубликатов, с учётом доверенности."""
    async with async_session() as db:
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=14)
        result = await db.execute(
            select(Message, Source)
            .join(Source, Message.source_id == Source.id)
            .where(
                Message.is_analyzed == True,
                Message.is_duplicate == False,
                Message.sentiment == "negative",
                Message.collected_at > cutoff,
            )
            .order_by(Message.published_at.desc())
            .limit(500)
        )
        rows = result.all()

    if not rows:
        logger.info("[Topics] Нет негативных сообщений для анализа")
        return

    trusted_rows = [(msg, src) for msg, src in rows if src.trust_score >= 20]
    if not trusted_rows:
        logger.info("[Topics] Нет сообщений от доверенных источников")
        return

    items = []
    for msg, source in trusted_rows:
        items.append(ProblemSourceInput(
            id=str(msg.id),
            text=msg.text,
            channel_name=source.name,
            channel_description=source.description or "",
            source_name=source.name,
            source_type=source.platform,
            source_url=source.source_url or "",
            published_at=msg.published_at,
        ))

    try:
        payload = ProblemCardsBuildRequest(
            items=items,
            top_k=10,
            similarity_threshold=0.78,
            time_window_days=14,
            negative_only=True,
            llm_item_analysis=True,
            llm_item_limit=30,
            llm_cluster_review=True,
            llm_cluster_review_limit=8,
        )
        async with _gigachat_lock:
            result = await build_problem_cards_llm(payload)
    except Exception as e:
        error_type = type(e).__name__
        if hasattr(e, 'status_code'):
            logger.error("[Topics] GigaChat ошибка | HTTP %s | %s: %s",
                         getattr(e, 'status_code', '?'), error_type, e)
        elif hasattr(e, 'response'):
            resp = getattr(e, 'response', None)
            status = resp.status_code if resp else '?'
            body = resp.text[:500] if resp else ''
            logger.error("[Topics] HTTP ошибка | %s | %s | body: %s", status, e, body)
        else:
            logger.error("[Topics] Ошибка | %s: %s", error_type, e)
        return

    cards = result.get("cards", []) if isinstance(result, dict) else []

    async with async_session() as db:
        old = await db.execute(select(Topic))
        for t in old.scalars().all():
            await db.delete(t)

        for card in cards[:10]:
            card_source_ids = card.get("source_ids", [])
            avg_trust = 50
            if card_source_ids:
                msg_ids = [int(sid) for sid in card_source_ids if str(sid).isdigit()]
                if msg_ids:
                    trust_result = await db.execute(
                        select(Source.trust_score)
                        .join(Message, Message.source_id == Source.id)
                        .where(Message.id.in_(msg_ids))
                    )
                    scores = [r[0] for r in trust_result.all() if r[0] is not None]
                    if scores:
                        avg_trust = sum(scores) // len(scores)

            trend_points = card.get("trend_points", [])
            trend_data = json.dumps(
                [{"date": str(p.get("date", "")), "mentions": p.get("mentions", 0)} for p in trend_points],
                ensure_ascii=False,
            ) if trend_points else None

            topic = Topic(
                title=card.get("title", "Без названия"),
                summary=card.get("summary"),
                category=card.get("category", "Другое"),
                region=card.get("region"),
                city=card.get("city"),
                district=card.get("district"),
                mentions_count=card.get("mentions_count", 0),
                negative_ratio=card.get("negative_ratio", 0.0),
                trend_direction=card.get("trend_direction", "flat"),
                rank_score=card.get("rank_score", 0.0),
                problem_signature=card.get("problem_signature"),
                keywords=json.dumps(card.get("key_words", []), ensure_ascii=False),
                first_seen_at=_parse_dt(card.get("first_seen_at")),
                last_seen_at=_parse_dt(card.get("last_seen_at")),
                peak_date=_parse_dt(card.get("peak_date")),
                peak_mentions=card.get("peak_mentions", 0),
                trend_data=trend_data,
                source_ids=json.dumps(card.get("source_ids", []), ensure_ascii=False),
            )
            db.add(topic)

        await db.commit()
        logger.info("[Topics] Построено %d топиков из %d негативных сообщений", min(len(cards), 10), len(trusted_rows))


def _parse_dt(s) -> datetime.datetime | None:
    if not s:
        return None
    try:
        return datetime.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None
