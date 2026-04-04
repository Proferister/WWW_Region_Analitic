import asyncio
import datetime
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from sqlalchemy import delete, select

from app.ai_analyze import close_service as close_ai_service
from app.analyzer import analyze_loop, build_topics_loop, gigachat_worker
from app.auth import router as auth_router
from app.collector import poll_rss_sources, save_max_message, save_tg_message
from app.config import settings
from app.dashboard import router as dashboard_router
from app.database import async_session, engine
from app.max_api import MaxAPI
from app.models import Base, OtpCode, RevokedToken, Source
from app.sources import router as sources_router
from app.telegram_api import TelegramAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api = MaxAPI(settings.MAX_BOT_TOKEN)
tg = TelegramAPI(settings.TG_BOT_TOKEN)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Таблицы БД созданы")

    # MAX webhook
    result = await api.subscribe_webhook(settings.WEBHOOK_URL)
    logger.info("MAX Webhook зарегистрирован: %s", result)

    # Telegram webhook
    result = await tg.set_webhook(settings.TG_WEBHOOK_URL)
    logger.info("Telegram Webhook зарегистрирован: %s", result)

    # Фоновые задачи
    tasks = [
        asyncio.create_task(cleanup_loop()),
        asyncio.create_task(poll_rss_sources()),
        asyncio.create_task(gigachat_worker()),  # Воркер очереди GigaChat (1 поток)
        asyncio.create_task(analyze_loop()),
        asyncio.create_task(build_topics_loop()),
    ]

    yield

    for t in tasks:
        t.cancel()
    await api.close()
    await tg.close()
    await close_ai_service()


async def cleanup_loop():
    """Фоновая задача: удаляет истёкшие OTP и старые отозванные токены каждый час."""
    while True:
        try:
            async with async_session() as db:
                now = datetime.datetime.now(datetime.timezone.utc)
                await db.execute(delete(OtpCode).where(OtpCode.expires_at < now))
                cutoff = now - datetime.timedelta(hours=48)
                await db.execute(delete(RevokedToken).where(RevokedToken.revoked_at < cutoff))
                await db.commit()
                logger.info("Очистка: удалены истёкшие OTP и старые отозванные токены")
        except Exception as e:
            logger.error("Ошибка очистки: %s", e)
        await asyncio.sleep(3600)


app = FastAPI(lifespan=lifespan)
app.include_router(auth_router)
app.include_router(sources_router)
app.include_router(dashboard_router)


# ==================== MAX WEBHOOK ====================

@app.post("/webhook")
async def max_webhook(request: Request):
    update = await request.json()
    update_type = update.get("update_type")
    logger.info("[MAX] update [%s]:\n%s", update_type, json.dumps(update, ensure_ascii=False, indent=2))

    if update_type == "bot_added":
        await max_bot_added(update)
    elif update_type == "bot_removed":
        await max_bot_removed(update)
    elif update_type == "bot_started":
        await max_bot_started(update)
    elif update_type == "message_callback":
        await max_callback(update)
    elif update_type == "message_created":
        await save_max_message(update)

    return {"ok": True}


async def max_bot_added(update: dict):
    chat_id = update.get("chat_id")
    user = update.get("user", {})
    first_name = user.get("first_name", "Неизвестно")
    last_name = user.get("last_name", "")
    user_name = f"{first_name} {last_name}".strip()

    title = "Неизвестная группа"
    description = None
    avatar_url = None
    if chat_id:
        try:
            chat = await api.get_chat(chat_id)
            title = chat.get("title") or title
            description = chat.get("description")
            icon = chat.get("icon")
            if icon:
                avatar_url = icon.get("url") or icon.get("urls", {}).get("small")
        except Exception as e:
            logger.error("[MAX] Ошибка получения чата %s: %s", chat_id, e)

    async with async_session() as db:
        result = await db.execute(
            select(Source).where(Source.source_id == str(chat_id), Source.platform == "max")
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.status = "pending"
            existing.name = title
            existing.description = description
            existing.avatar_url = avatar_url
        else:
            db.add(Source(
                platform="max", name=title, description=description,
                avatar_url=avatar_url,
                source_id=str(chat_id), status="pending",
            ))
        await db.commit()

    logger.info("[MAX] Бот добавлен | Группа: %s | Добавил: %s | chat_id: %s", title, user_name, chat_id)


async def max_bot_removed(update: dict):
    chat_id = update.get("chat_id")
    if not chat_id:
        return
    async with async_session() as db:
        result = await db.execute(
            select(Source).where(Source.source_id == str(chat_id), Source.platform == "max")
        )
        source = result.scalar_one_or_none()
        if source:
            await db.delete(source)
            await db.commit()
            logger.info("[MAX] Бот удалён — источник удалён | chat_id: %s | %s", chat_id, source.name)


async def max_callback(update: dict):
    callback = update.get("callback", {})
    callback_id = callback.get("callback_id")
    payload = callback.get("payload", "")
    if ":" not in payload:
        return
    action, chat_id_str = payload.split(":", 1)
    try:
        chat_id = int(chat_id_str)
    except ValueError:
        return

    async with async_session() as db:
        result = await db.execute(
            select(Source).where(Source.source_id == str(chat_id), Source.platform == "max")
        )
        source = result.scalar_one_or_none()
        if not source:
            await api.answer_callback(callback_id, notification="Источник не найден")
            return

        if action == "approve":
            source.status = "approved"
            source.is_active = True
            await db.commit()
            await api.answer_callback(callback_id, notification=f"Группа «{source.name}» подключена!")
            logger.info("[MAX] Источник подключён: %s", source.name)
        elif action == "reject":
            source.status = "rejected"
            source.is_active = False
            await db.commit()
            await api.answer_callback(callback_id, notification=f"Группа «{source.name}» отклонена.")
            logger.info("[MAX] Источник отклонён: %s", source.name)
            try:
                await api.leave_chat(chat_id)
            except Exception:
                pass


async def max_bot_started(update: dict):
    user = update.get("user", {})
    user_id = user.get("user_id")
    first_name = user.get("first_name", "")
    greeting = (
        f"Здравствуйте, {first_name}! 👋\n\n"
        f"Добро пожаловать в систему аналитики региональных новостей и обращений граждан.\n\n"
        f"🔹 **Для сотрудников** — войдите через рабочую почту, чтобы получить полный доступ к аналитике, "
        f"отчётам и управлению источниками.\n\n"
        f"🔹 **Для гостей** — вы можете ознакомиться с общедоступной сводкой в гостевом режиме.\n\n"
        f"Нажмите кнопку ниже, чтобы открыть мини-приложение 👇"
    )
    try:
        await api.send_message(user_id=user_id, text=greeting)
        logger.info("[MAX] Приветствие отправлено: %s (%s)", first_name, user_id)
    except Exception as e:
        logger.error("[MAX] Ошибка приветствия %s: %s", user_id, e)


# ==================== TELEGRAM WEBHOOK ====================

@app.post("/tg-webhook")
async def telegram_webhook(request: Request):
    update = await request.json()
    logger.info("[TG] update:\n%s", json.dumps(update, ensure_ascii=False, indent=2))

    message = update.get("message", {})
    my_chat_member = update.get("my_chat_member")

    # Бот добавлен/удалён из группы
    if my_chat_member:
        await tg_chat_member_update(my_chat_member)
    # Команда /start в личке
    elif message.get("text", "").startswith("/start") and message.get("chat", {}).get("type") == "private":
        await tg_start(message)
    # Сообщение в группе/канале — сохранить для анализа
    elif message.get("text") or update.get("channel_post", {}).get("text"):
        await save_tg_message(update)

    return {"ok": True}


async def tg_chat_member_update(data: dict):
    chat = data.get("chat", {})
    chat_id = chat.get("id")
    chat_title = chat.get("title", "Неизвестная группа")
    chat_type = chat.get("type", "")

    # Только группы и супергруппы
    if chat_type not in ("group", "supergroup"):
        return

    new_status = data.get("new_chat_member", {}).get("status", "")
    old_status = data.get("old_chat_member", {}).get("status", "")
    from_user = data.get("from", {})
    user_name = f"{from_user.get('first_name', '')} {from_user.get('last_name', '')}".strip()

    if new_status in ("member", "administrator"):
        # Получить аватарку
        avatar_url = None
        try:
            avatar_url = await tg.get_chat_avatar_url(chat_id)
        except Exception:
            pass

        # Бот добавлен в группу
        async with async_session() as db:
            result = await db.execute(
                select(Source).where(Source.source_id == str(chat_id), Source.platform == "telegram")
            )
            existing = result.scalar_one_or_none()
            if existing:
                existing.status = "pending"
                existing.name = chat_title
                existing.avatar_url = avatar_url
            else:
                db.add(Source(
                    platform="telegram", name=chat_title,
                    avatar_url=avatar_url,
                    source_id=str(chat_id), status="pending",
                ))
            await db.commit()

        logger.info("[TG] Бот добавлен | Группа: %s | Добавил: %s | chat_id: %s", chat_title, user_name, chat_id)

    elif new_status in ("left", "kicked"):
        # Бот удалён из группы
        async with async_session() as db:
            result = await db.execute(
                select(Source).where(Source.source_id == str(chat_id), Source.platform == "telegram")
            )
            source = result.scalar_one_or_none()
            if source:
                await db.delete(source)
                await db.commit()
                logger.info("[TG] Бот удалён — источник удалён | chat_id: %s | %s", chat_id, source.name)


async def tg_start(message: dict):
    chat_id = message["chat"]["id"]
    first_name = message["from"].get("first_name", "")
    greeting = (
        f"Здравствуйте, {first_name}! 👋\n\n"
        f"Добро пожаловать в систему аналитики региональных новостей и обращений граждан.\n\n"
        f"Для полного доступа используйте бота в мессенджере MAX:\n"
        f"👉 [Открыть в MAX](https://max.ru/id616483986174_bot)\n\n"
        f"Или откройте веб-версию:\n"
        f"🌐 [whitea.ru](https://whitea.ru)"
    )
    try:
        await tg.send_message(chat_id=chat_id, text=greeting)
        logger.info("[TG] Приветствие отправлено: %s (%s)", first_name, chat_id)
    except Exception as e:
        logger.error("[TG] Ошибка приветствия %s: %s", chat_id, e)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, root_path="/api", reload=True)
