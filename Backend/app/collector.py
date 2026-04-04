"""Сбор сообщений из источников: MAX webhook, Telegram webhook, RSS polling."""
import asyncio
import datetime
import hashlib
import json
import logging
import re
import xml.etree.ElementTree as ET

import httpx
from sqlalchemy import select

from app.database import async_session
from app.models import Message, Source

logger = logging.getLogger(__name__)


def _text_hash(text: str) -> str:
    """Нормализованный SHA256 хеш текста для дедупликации."""
    normalized = re.sub(r'\s+', ' ', text.strip().lower())
    return hashlib.sha256(normalized.encode()).hexdigest()


def _normalize(text: str) -> str:
    """Нормализация текста для сравнения."""
    return re.sub(r'\s+', ' ', text.strip().lower())


def _text_similarity(a: str, b: str) -> float:
    """Коэффициент схожести двух текстов (0.0 - 1.0) через пересечение слов."""
    words_a = set(_normalize(a).split())
    words_b = set(_normalize(b).split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)  # Jaccard


async def _is_duplicate(db, text: str, text_hash: str) -> bool:
    """Проверить: точный дубликат по хешу ИЛИ 80%+ схожесть с последними сообщениями."""
    # 1. Точный дубликат
    result = await db.execute(
        select(Message.id).where(Message.text_hash == text_hash).limit(1)
    )
    if result.scalar_one_or_none() is not None:
        return True

    # 2. Проверка схожести с последними 200 сообщениями
    result = await db.execute(
        select(Message.text)
        .where(Message.is_duplicate == False)
        .order_by(Message.collected_at.desc())
        .limit(200)
    )
    recent_texts = [r[0] for r in result.all()]

    for existing_text in recent_texts:
        if _text_similarity(text, existing_text) >= 0.20:
            return True

    return False


# ==================== WEBHOOK СООБЩЕНИЯ (MAX / TG) ====================

async def save_max_message(update: dict):
    """Сохранить сообщение из MAX чата (message_created)."""
    body = update.get("message", {}).get("body", {})
    text = body.get("text", "")
    if not text or not text.strip():
        return

    chat_id = str(update.get("message", {}).get("recipient", {}).get("chat_id", ""))
    sender = update.get("message", {}).get("sender", {})
    author = f"{sender.get('first_name', '')} {sender.get('last_name', '')}".strip()
    msg_id = body.get("mid", "")
    timestamp = update.get("message", {}).get("timestamp")

    published = None
    if timestamp:
        published = datetime.datetime.fromtimestamp(timestamp / 1000, tz=datetime.timezone.utc)

    async with async_session() as db:
        # Найти approved источник
        result = await db.execute(
            select(Source).where(
                Source.source_id == chat_id,
                Source.platform == "max",
                Source.status == "approved",
            )
        )
        source = result.scalar_one_or_none()
        if not source:
            return

        # Проверить дубликат по external_id
        if msg_id:
            existing = await db.execute(
                select(Message).where(Message.external_id == str(msg_id), Message.source_id == source.id)
            )
            if existing.scalar_one_or_none():
                return

        # Проверить дубликат по хешу текста (кросс-источники)
        th = _text_hash(text)
        is_dup = await _is_duplicate(db, text, th)

        msg = Message(
            source_id=source.id,
            external_id=str(msg_id) if msg_id else None,
            text=text.strip(),
            text_hash=th,
            is_duplicate=is_dup,
            author_name=author or None,
            published_at=published,
        )
        db.add(msg)
        await db.commit()
        if is_dup:
            logger.info("[MAX] Дубликат обнаружен | chat: %s", chat_id)
        else:
            logger.info("[MAX] Сообщение сохранено | chat: %s | author: %s", chat_id, author)


async def save_tg_message(update: dict):
    """Сохранить сообщение из Telegram чата."""
    message = update.get("message") or update.get("channel_post")
    if not message:
        return

    text = message.get("text", "")
    if not text or not text.strip():
        return

    chat = message.get("chat", {})
    chat_id = str(chat.get("id", ""))
    chat_type = chat.get("type", "")
    if chat_type not in ("group", "supergroup", "channel"):
        return

    from_user = message.get("from", {})
    author = f"{from_user.get('first_name', '')} {from_user.get('last_name', '')}".strip()
    msg_id = str(message.get("message_id", ""))
    date = message.get("date")

    published = None
    if date:
        published = datetime.datetime.fromtimestamp(date, tz=datetime.timezone.utc)

    async with async_session() as db:
        result = await db.execute(
            select(Source).where(
                Source.source_id == chat_id,
                Source.platform == "telegram",
                Source.status == "approved",
            )
        )
        source = result.scalar_one_or_none()
        if not source:
            return

        if msg_id:
            existing = await db.execute(
                select(Message).where(Message.external_id == msg_id, Message.source_id == source.id)
            )
            if existing.scalar_one_or_none():
                return

        th = _text_hash(text)
        is_dup = await _is_duplicate(db, text, th)

        msg = Message(
            source_id=source.id,
            external_id=msg_id or None,
            text=text.strip(),
            text_hash=th,
            is_duplicate=is_dup,
            author_name=author or None,
            published_at=published,
        )
        db.add(msg)
        await db.commit()
        if is_dup:
            logger.info("[TG] Дубликат обнаружен | chat: %s", chat_id)
        else:
            logger.info("[TG] Сообщение сохранено | chat: %s | author: %s", chat_id, author)


# ==================== RSS POLLING ====================

async def poll_rss_sources():
    """Фоновый цикл опроса RSS-источников каждые 10 минут."""
    while True:
        try:
            async with async_session() as db:
                result = await db.execute(
                    select(Source).where(
                        Source.platform == "rss",
                        Source.status == "approved",
                        Source.is_active == True,
                    )
                )
                sources = result.scalars().all()

            for source in sources:
                try:
                    await _fetch_rss(source)
                except Exception as e:
                    logger.error("[RSS] Ошибка опроса %s: %s", source.name, e)

        except Exception as e:
            logger.error("[RSS] Ошибка цикла: %s", e)

        await asyncio.sleep(600)  # 10 минут


async def _fetch_rss(source: Source):
    """Загрузить и сохранить новые записи из RSS/ATOM фида."""
    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
        resp = await client.get(source.source_id)  # source_id = URL фида
        resp.raise_for_status()

    # Исправить незакрытые теги (WordPress RSS)
    text_content = resp.text
    for tag in ("atom:link", "enclosure"):
        text_content = re.sub(rf'(<{re.escape(tag)}\b[^>]*?)(?<!/)>', r'\1/>', text_content)

    try:
        root = ET.fromstring(text_content)
    except ET.ParseError:
        return

    items = []

    # RSS 2.0
    if root.tag == "rss":
        for item in root.findall(".//item"):
            items.append({
                "title": _el_text(item, "title"),
                "description": _el_text(item, "description"),
                "link": _el_text(item, "link"),
                "guid": _el_text(item, "guid") or _el_text(item, "link"),
                "pubDate": _el_text(item, "pubDate"),
            })

    # ATOM
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    if root.tag in ("{http://www.w3.org/2005/Atom}feed", "feed"):
        for entry in root.findall("atom:entry", ns) or root.findall("entry"):
            link_el = entry.find("atom:link[@rel='alternate']", ns) or entry.find("atom:link", ns)
            if link_el is None:
                link_el = entry.find("link[@rel='alternate']") or entry.find("link")
            link = link_el.get("href") if link_el is not None else None

            items.append({
                "title": _el_text_ns(entry, "atom:title", ns) or _el_text(entry, "title"),
                "description": _el_text_ns(entry, "atom:summary", ns) or _el_text(entry, "summary"),
                "link": link,
                "guid": _el_text_ns(entry, "atom:id", ns) or _el_text(entry, "id") or link,
                "pubDate": _el_text_ns(entry, "atom:published", ns) or _el_text_ns(entry, "atom:updated", ns),
            })

    if not items:
        return

    saved = 0
    async with async_session() as db:
        for item in items[:50]:  # макс 50 за раз
            text = item.get("title", "") or ""
            desc = item.get("description", "") or ""
            if desc and desc != text:
                text = f"{text}\n{desc}" if text else desc
            text = text.strip()
            if not text:
                continue

            guid = item.get("guid", "") or item.get("link", "")
            if guid:
                existing = await db.execute(
                    select(Message).where(Message.external_id == guid, Message.source_id == source.id)
                )
                if existing.scalar_one_or_none():
                    continue

            th = _text_hash(text)
            is_dup = await _is_duplicate(db, text, th)

            msg = Message(
                source_id=source.id,
                external_id=guid or None,
                text=text,
                text_hash=th,
                is_duplicate=is_dup,
                published_at=_parse_date(item.get("pubDate")),
            )
            db.add(msg)
            saved += 1

        if saved:
            await db.commit()
            logger.info("[RSS] Сохранено %d новых записей | %s", saved, source.name)


def _el_text(el, path):
    child = el.find(path)
    return child.text.strip() if child is not None and child.text else None


def _el_text_ns(el, path, ns):
    child = el.find(path, ns)
    return child.text.strip() if child is not None and child.text else None


def _parse_date(s: str | None) -> datetime.datetime | None:
    if not s:
        return None
    from email.utils import parsedate_to_datetime
    try:
        return parsedate_to_datetime(s)
    except Exception:
        pass
    try:
        return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None
