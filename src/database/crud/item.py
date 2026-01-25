from datetime import datetime

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.enums import Category, ItemStatus
from database.models import Item

PAGE_SIZE = 20
MAX_TITLE_LENGTH = 100


async def create_item(
    user_id: int,
    title: str,
    category: Category,
    session: AsyncSession,
    *,
    status: ItemStatus = ItemStatus.BACKLOG,
) -> Item:
    item = Item(
        user_id=user_id,
        title=title,
        category=category,
        status=status,
        logged_at=datetime.now() if status == ItemStatus.LOGGED else None,
    )
    session.add(item)
    await session.flush()
    return item


async def get_item(item_id: int, session: AsyncSession) -> Item | None:
    result = await session.execute(select(Item).where(Item.id == item_id))
    return result.scalar_one_or_none()


async def get_items(
    user_id: int,
    category: Category,
    status: ItemStatus,
    session: AsyncSession,
    *,
    page: int = 0,
) -> list[Item]:
    result = await session.execute(
        select(Item)
        .where(Item.user_id == user_id, Item.category == category, Item.status == status)
        .order_by(Item.created_at.desc())
        .offset(page * PAGE_SIZE)
        .limit(PAGE_SIZE)
    )
    return list(result.scalars().all())


async def get_items_count(
    user_id: int,
    category: Category,
    status: ItemStatus,
    session: AsyncSession,
) -> int:
    result = await session.execute(
        select(func.count(Item.id)).where(
            Item.user_id == user_id,
            Item.category == category,
            Item.status == status,
        )
    )
    return result.scalar_one()


async def log_item(item_id: int, session: AsyncSession) -> Item | None:
    item = await get_item(item_id, session)
    if item:
        item.status = ItemStatus.LOGGED
        item.logged_at = datetime.now()
        await session.flush()
    return item


async def update_item_title(item_id: int, title: str, session: AsyncSession) -> Item | None:
    item = await get_item(item_id, session)
    if item:
        item.title = title
        await session.flush()
    return item


async def delete_item(item_id: int, session: AsyncSession) -> bool:
    item = await get_item(item_id, session)
    if item:
        await session.delete(item)
        await session.flush()
        return True
    return False


# Statistics
async def get_stats(user_id: int, session: AsyncSession, year: int | None = None) -> dict:
    """Get user statistics by category."""
    stats = {}
    for cat in Category:
        query = select(func.count(Item.id)).where(
            Item.user_id == user_id,
            Item.category == cat,
            Item.status == ItemStatus.LOGGED,
        )
        if year:
            query = query.where(extract("year", Item.logged_at) == year)

        result = await session.execute(query)
        stats[cat] = result.scalar_one()

    return stats


async def get_total_stats(user_id: int, session: AsyncSession) -> dict:
    """Get total counts for backlog and logged."""
    backlog = await session.execute(
        select(func.count(Item.id)).where(
            Item.user_id == user_id,
            Item.status == ItemStatus.BACKLOG,
        )
    )
    logged = await session.execute(
        select(func.count(Item.id)).where(
            Item.user_id == user_id,
            Item.status == ItemStatus.LOGGED,
        )
    )
    return {
        "backlog": backlog.scalar_one(),
        "logged": logged.scalar_one(),
    }
