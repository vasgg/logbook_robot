import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.dispatcher.event.bases import UNHANDLED
from aiogram.types import TelegramObject, Update

logger = logging.getLogger(__name__)


class UpdatesDumperMiddleware(BaseMiddleware):
    """Logs all incoming updates as JSON. Use in dev mode only."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        logger.debug(event.model_dump_json(exclude_unset=True))
        result = await handler(event, data)
        if result is UNHANDLED:
            logger.warning("Update not handled: %s", event.update_id)
        return result
