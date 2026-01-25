import html
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import Message

from bot.config import APP_NAME, Settings

logger = logging.getLogger(__name__)


async def on_startup(bot: Bot, settings: Settings) -> None:
    try:
        await bot.send_message(
            settings.bot_admin,
            f"<b>{APP_NAME} started</b>\n\n/start",
            disable_notification=True,
        )
    except Exception:
        logger.warning("Failed to send startup notification")


async def on_shutdown(bot: Bot, settings: Settings) -> None:
    try:
        await bot.send_message(
            settings.bot_admin,
            f"<b>{APP_NAME} shutdown</b>",
            disable_notification=True,
        )
    except Exception:
        logger.warning("Failed to send shutdown notification")


async def notify_admin(bot: Bot, admin_id: int, text: str) -> None:
    try:
        await bot.send_message(
            admin_id,
            text,
            disable_web_page_preview=True,
        )
    except Exception:
        logger.warning("Failed to notify admin: %s", text[:50])


async def send_message_safe(
    bot: Bot,
    user_id: int,
    text: str,
    admin_id: int | None = None,
    fullname: str | None = None,
    **kwargs,
) -> Message | None:
    """Send message with blocked user handling."""
    try:
        return await bot.send_message(chat_id=user_id, text=text, **kwargs)
    except TelegramForbiddenError:
        logger.warning("User %s blocked bot", user_id)
        if admin_id and fullname:
            warning = (
                "<b>Message delivery failed</b>\n"
                f"User: <b>{html.escape(fullname)}</b>\n"
                f"<pre>{html.escape(text[:500])}</pre>"
            )
            await notify_admin(bot, admin_id, warning)
        return None
