from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import main_menu_kb, stats_kb
from database.crud.item import get_logged_years, get_total_stats
from database.models import User

router = Router()


@router.message(CommandStart())
async def start_cmd(message: Message, user: User) -> None:
    await message.answer(
        text=f"Hi, {user.fullname}!\nChoose a category:",
        reply_markup=main_menu_kb(),
    )


@router.message(Command("stats"))
async def stats_cmd(message: Message, user: User, session: AsyncSession) -> None:
    totals = await get_total_stats(user.id, session)
    years = await get_logged_years(user.id, session)

    text = f"<b>Your stats</b>\n\nBacklog: {totals['backlog']}\nLogged: {totals['logged']}"

    if years:
        await message.answer(text=text, reply_markup=stats_kb(years))
    else:
        text += "\n\n<i>No logged items yet to show yearly stats.</i>"
        await message.answer(text=text, reply_markup=main_menu_kb())
