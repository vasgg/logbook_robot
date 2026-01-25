from aiogram.types import User as TgUser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User


async def get_user(user_id: int, session: AsyncSession) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(tg_user: TgUser, session: AsyncSession) -> User:
    user = User(
        id=tg_user.id,
        fullname=tg_user.full_name,
        username=tg_user.username,
    )
    session.add(user)
    await session.flush()
    return user
