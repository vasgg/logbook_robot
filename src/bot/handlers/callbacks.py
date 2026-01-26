from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.enums import Category, ItemStatus
from bot.keyboards.inline import (
    CATEGORY_EMOJI,
    ItemCb,
    MenuCb,
    cancel_edit_kb,
    cancel_kb,
    category_menu_kb,
    item_detail_kb,
    items_list_kb,
    main_menu_kb,
    stats_kb,
    stats_year_kb,
)
from database.crud.item import (
    MAX_TITLE_LENGTH,
    PAGE_SIZE,
    create_item,
    delete_item,
    get_item,
    get_items,
    get_items_count,
    get_logged_years,
    get_stats,
    get_total_stats,
    log_item,
    update_item_title,
)
from database.models import User

router = Router()


class AddItem(StatesGroup):
    title = State()


class EditItem(StatesGroup):
    title = State()


@router.callback_query(MenuCb.filter(F.action == "main"))
async def main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(text="Choose a category:", reply_markup=main_menu_kb())


@router.callback_query(MenuCb.filter(F.action == "category"))
async def category_menu(callback: CallbackQuery, callback_data: MenuCb, user: User, session: AsyncSession) -> None:
    category = Category(callback_data.category)
    backlog = await get_items_count(user.id, category, ItemStatus.BACKLOG, session)
    logged = await get_items_count(user.id, category, ItemStatus.LOGGED, session)
    await callback.message.edit_text(
        text=f"{category.value.capitalize()}:",
        reply_markup=category_menu_kb(category.value, backlog, logged),
    )


@router.callback_query(MenuCb.filter(F.action == "backlog"))
async def backlog_list(callback: CallbackQuery, callback_data: MenuCb, user: User, session: AsyncSession) -> None:
    category = Category(callback_data.category)
    page = callback_data.page
    items = await get_items(user.id, category, ItemStatus.BACKLOG, session, page=page)
    total = await get_items_count(user.id, category, ItemStatus.BACKLOG, session)

    text = f"Backlog ({total}):" if items else "Backlog is empty"
    await callback.message.edit_text(
        text=text,
        reply_markup=items_list_kb(items, category.value, ItemStatus.BACKLOG, page, total, PAGE_SIZE),
    )


@router.callback_query(MenuCb.filter(F.action == "logged"))
async def logged_list(callback: CallbackQuery, callback_data: MenuCb, user: User, session: AsyncSession) -> None:
    category = Category(callback_data.category)
    page = callback_data.page
    items = await get_items(user.id, category, ItemStatus.LOGGED, session, page=page)
    total = await get_items_count(user.id, category, ItemStatus.LOGGED, session)

    text = f"Logged ({total}):" if items else "Nothing logged yet"
    await callback.message.edit_text(
        text=text,
        reply_markup=items_list_kb(items, category.value, ItemStatus.LOGGED, page, total, PAGE_SIZE),
    )


@router.callback_query(ItemCb.filter(F.action.in_({"add_backlog", "add_logged"})))
async def add_item_start(callback: CallbackQuery, callback_data: ItemCb, state: FSMContext) -> None:
    target_status = ItemStatus.BACKLOG if callback_data.action == "add_backlog" else ItemStatus.LOGGED
    await state.set_state(AddItem.title)
    await state.update_data(category=callback_data.category, target_status=target_status.value)
    await callback.message.edit_text(text="Enter title:", reply_markup=cancel_kb())


@router.message(AddItem.title)
async def add_item_title(message: Message, state: FSMContext, user: User, session: AsyncSession) -> None:
    data = await state.get_data()
    category = Category(data["category"])
    target_status = ItemStatus(data["target_status"])

    title = message.text.strip()[:MAX_TITLE_LENGTH]
    if not title:
        await message.answer("Title cannot be empty. Try again:", reply_markup=cancel_kb())
        return

    await create_item(user.id, title, category, session, status=target_status)
    await state.clear()

    backlog = await get_items_count(user.id, category, ItemStatus.BACKLOG, session)
    logged = await get_items_count(user.id, category, ItemStatus.LOGGED, session)

    status_text = "backlog" if target_status == ItemStatus.BACKLOG else "logged"
    await message.answer(
        text=f"Added to {status_text}!\n\n{category.value.capitalize()}:",
        reply_markup=category_menu_kb(category.value, backlog, logged),
    )


@router.callback_query(ItemCb.filter(F.action == "view"))
async def view_item(callback: CallbackQuery, callback_data: ItemCb, session: AsyncSession) -> None:
    item = await get_item(callback_data.id, session)
    if not item:
        await callback.answer("Item not found")
        return

    date_str = item.created_at.strftime("%Y-%m-%d")
    await callback.message.edit_text(
        text=f"<b>{item.title}</b>\n{date_str}",
        reply_markup=item_detail_kb(item.id, item.category.value, item.status, callback_data.page),
    )


@router.callback_query(ItemCb.filter(F.action == "edit"))
async def edit_item_start(callback: CallbackQuery, callback_data: ItemCb, state: FSMContext) -> None:
    await state.set_state(EditItem.title)
    await state.update_data(item_id=callback_data.id, page=callback_data.page)
    await callback.message.edit_text(
        text="Enter new title:",
        reply_markup=cancel_edit_kb(callback_data.id),
    )


@router.message(EditItem.title)
async def edit_item_title(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    item_id = data["item_id"]
    page = data["page"]

    title = message.text.strip()[:MAX_TITLE_LENGTH]
    if not title:
        await message.answer("Title cannot be empty. Try again:", reply_markup=cancel_edit_kb(item_id))
        return

    item = await update_item_title(item_id, title, session)
    await state.clear()

    if not item:
        await message.answer("Item not found", reply_markup=main_menu_kb())
        return

    date_str = item.created_at.strftime("%Y-%m-%d")
    await message.answer(
        text=f"Updated!\n\n<b>{item.title}</b>\n{date_str}",
        reply_markup=item_detail_kb(item.id, item.category.value, item.status, page),
    )


@router.callback_query(ItemCb.filter(F.action == "log"))
async def log_item_cb(callback: CallbackQuery, callback_data: ItemCb, user: User, session: AsyncSession) -> None:
    item = await log_item(callback_data.id, session)
    if not item:
        await callback.answer("Item not found")
        return

    await callback.answer("Logged!")
    page = callback_data.page
    items = await get_items(user.id, item.category, ItemStatus.BACKLOG, session, page=page)
    total = await get_items_count(user.id, item.category, ItemStatus.BACKLOG, session)

    text = f"Backlog ({total}):" if items else "Backlog is empty"
    await callback.message.edit_text(
        text=text,
        reply_markup=items_list_kb(items, item.category.value, ItemStatus.BACKLOG, page, total, PAGE_SIZE),
    )


@router.callback_query(ItemCb.filter(F.action == "delete"))
async def delete_item_cb(callback: CallbackQuery, callback_data: ItemCb, user: User, session: AsyncSession) -> None:
    item = await get_item(callback_data.id, session)
    if not item:
        await callback.answer("Item not found")
        return

    category = item.category
    status = item.status
    await delete_item(callback_data.id, session)

    await callback.answer("Deleted!")
    page = callback_data.page
    items = await get_items(user.id, category, status, session, page=page)
    total = await get_items_count(user.id, category, status, session)

    text = f"{status.value.capitalize()} ({total}):" if items else f"{status.value.capitalize()} is empty"
    await callback.message.edit_text(
        text=text,
        reply_markup=items_list_kb(items, category.value, status, page, total, PAGE_SIZE),
    )


# Stats handlers
@router.callback_query(MenuCb.filter(F.action == "stats"))
async def stats_menu(callback: CallbackQuery, user: User, session: AsyncSession) -> None:
    totals = await get_total_stats(user.id, session)
    years = await get_logged_years(user.id, session)

    text = f"<b>Your stats</b>\n\nBacklog: {totals['backlog']}\nLogged: {totals['logged']}"

    if years:
        await callback.message.edit_text(text=text, reply_markup=stats_kb(years))
    else:
        text += "\n\n<i>No logged items yet to show yearly stats.</i>"
        await callback.message.edit_text(text=text, reply_markup=main_menu_kb())


@router.callback_query(MenuCb.filter(F.action == "stats_year"))
async def stats_year(callback: CallbackQuery, callback_data: MenuCb, user: User, session: AsyncSession) -> None:
    year = callback_data.year
    stats = await get_stats(user.id, session, year=year)

    lines = [f"<b>Logged in {year}</b>\n"]
    total = 0
    for cat, count in stats.items():
        lines.append(f"{CATEGORY_EMOJI[cat]} {cat.value.capitalize()}: {count}")
        total += count
    lines.append(f"\nTotal: {total}")

    await callback.message.edit_text(text="\n".join(lines), reply_markup=stats_year_kb(year))
