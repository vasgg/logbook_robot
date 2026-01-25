from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.user import create_user, get_user


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        session: AsyncSession = data["session"]
        tg_user = data.get("event_from_user")

        if tg_user is None:
            return await handler(event, data)

        user = await get_user(tg_user.id, session)
        if user is None:
            user = await create_user(tg_user, session)

        data["user"] = user
        return await handler(event, data)
