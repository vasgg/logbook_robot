import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """Logs handler calls with timing."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        start = time.perf_counter()
        user = getattr(event, "from_user", None)
        user_info = f"user={user.id}" if user else "user=?"

        if isinstance(event, Message):
            event_info = f"message: {event.text[:30] if event.text else '[no text]'!r}"
        elif isinstance(event, CallbackQuery):
            event_info = f"callback: {event.data}"
        else:
            event_info = f"{type(event).__name__}"

        result = await handler(event, data)

        elapsed = (time.perf_counter() - start) * 1000
        logger.info("%s | %s | %.1fms", user_info, event_info, elapsed)

        return result
