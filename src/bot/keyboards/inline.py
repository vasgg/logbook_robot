from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.enums import Category, ItemStatus


class MenuCb(CallbackData, prefix="m"):
    action: str
    category: str | None = None
    page: int = 0
    year: int | None = None


class ItemCb(CallbackData, prefix="i"):
    action: str
    id: int | None = None
    category: str | None = None
    page: int = 0


CATEGORY_EMOJI = {
    Category.BOOKS: "\U0001f4da",
    Category.MOVIES: "\U0001f3ac",
    Category.SERIES: "\U0001f4fa",
    Category.GAMES: "\U0001f3ae",
}


def main_menu_kb():
    builder = InlineKeyboardBuilder()
    for cat in Category:
        builder.button(
            text=f"{CATEGORY_EMOJI[cat]} {cat.value.capitalize()}",
            callback_data=MenuCb(action="category", category=cat.value),
        )
    builder.adjust(1)
    return builder.as_markup()


def category_menu_kb(category: str, backlog_count: int, logged_count: int):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="\u2795 Backlog",
        callback_data=ItemCb(action="add_backlog", category=category),
    )
    builder.button(
        text="\u2795 Log",
        callback_data=ItemCb(action="add_logged", category=category),
    )
    builder.button(
        text=f"\U0001f4cb Show Backlog ({backlog_count})",
        callback_data=MenuCb(action="backlog", category=category),
    )
    builder.button(
        text=f"\u2705 Show Logged ({logged_count})",
        callback_data=MenuCb(action="logged", category=category),
    )
    builder.button(
        text="\u2b05 Back",
        callback_data=MenuCb(action="main"),
    )
    builder.adjust(2, 1, 1, 1)
    return builder.as_markup()


def items_list_kb(items: list, category: str, status: ItemStatus, page: int, total: int, page_size: int):
    builder = InlineKeyboardBuilder()
    emoji = CATEGORY_EMOJI[Category(category)]
    for item in items:
        builder.button(text=f"{emoji} {item.title}", callback_data=ItemCb(action="view", id=item.id, page=page))

    # Pagination
    has_prev = page > 0
    has_next = (page + 1) * page_size < total

    if has_prev or has_next:
        if has_prev:
            builder.button(text="\u25c0", callback_data=MenuCb(action=status.value, category=category, page=page - 1))
        if has_next:
            builder.button(text="\u25b6", callback_data=MenuCb(action=status.value, category=category, page=page + 1))

    builder.button(
        text="\u2b05 Back",
        callback_data=MenuCb(action="category", category=category),
    )

    # Adjust: items 1 per row, pagination buttons together, back alone
    rows = [1] * len(items)
    if has_prev or has_next:
        rows.append(2 if has_prev and has_next else 1)
    rows.append(1)
    builder.adjust(*rows)

    return builder.as_markup()


def item_detail_kb(item_id: int, category: str, status: ItemStatus, page: int = 0):
    builder = InlineKeyboardBuilder()
    if status == ItemStatus.BACKLOG:
        builder.button(
            text="\u2705 Log",
            callback_data=ItemCb(action="log", id=item_id, page=page),
        )
    builder.button(
        text="\u270f\ufe0f",
        callback_data=ItemCb(action="edit", id=item_id, page=page),
    )
    builder.button(
        text="\U0001f5d1",
        callback_data=ItemCb(action="delete", id=item_id, page=page),
    )
    builder.button(
        text="\u2b05 Back",
        callback_data=MenuCb(action=status.value, category=category, page=page),
    )
    # 3 buttons for backlog (Log, Edit, Delete), 2 for logged (Edit, Delete)
    builder.adjust(3 if status == ItemStatus.BACKLOG else 2, 1)
    return builder.as_markup()


def cancel_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="\u274c Cancel", callback_data=MenuCb(action="main"))
    return builder.as_markup()


def cancel_edit_kb(item_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="\u274c Cancel", callback_data=ItemCb(action="view", id=item_id))
    return builder.as_markup()


def stats_kb(years: list[int]):
    builder = InlineKeyboardBuilder()
    for year in years:
        builder.button(
            text=f"\U0001f4c5 {year}",
            callback_data=MenuCb(action="stats_year", year=year),
        )
    builder.button(
        text="\u2b05 Back",
        callback_data=MenuCb(action="main"),
    )
    # Years in rows of 2, back button alone
    rows = [2] * (len(years) // 2)
    if len(years) % 2:
        rows.append(1)
    rows.append(1)
    builder.adjust(*rows)
    return builder.as_markup()


def stats_year_kb(year: int):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="\u2b05 Back",
        callback_data=MenuCb(action="stats"),
    )
    return builder.as_markup()
