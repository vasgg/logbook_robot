from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

MAIN_WINDOW_CHAT_ID_KEY = "main_window_chat_id"
MAIN_WINDOW_MESSAGE_ID_KEY = "main_window_message_id"


def _message_ref(message: Message) -> tuple[int, int]:
    return message.chat.id, message.message_id


def _main_window_from_data(data: dict[str, object]) -> tuple[int, int] | None:
    chat_id = data.get(MAIN_WINDOW_CHAT_ID_KEY)
    message_id = data.get(MAIN_WINDOW_MESSAGE_ID_KEY)
    if not isinstance(chat_id, int) or not isinstance(message_id, int):
        return None
    return chat_id, message_id


async def get_main_window(state: FSMContext) -> tuple[int, int] | None:
    return _main_window_from_data(await state.get_data())


async def set_main_window(state: FSMContext, chat_id: int, message_id: int) -> None:
    await state.update_data(
        **{
            MAIN_WINDOW_CHAT_ID_KEY: chat_id,
            MAIN_WINDOW_MESSAGE_ID_KEY: message_id,
        }
    )


async def clear_flow_state(state: FSMContext) -> None:
    main_window = await get_main_window(state)
    await state.clear()
    if main_window is not None:
        await set_main_window(state, *main_window)


async def _try_edit_message(
    bot: Bot,
    chat_id: int,
    message_id: int,
    text: str,
    reply_markup: InlineKeyboardMarkup | None,
) -> bool:
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=reply_markup,
        )
    except TelegramBadRequest as exc:
        return "message is not modified" in str(exc).lower()

    return True


async def _try_clear_keyboard(bot: Bot, chat_id: int, message_id: int) -> None:
    try:
        await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
    except TelegramBadRequest:
        return


async def _render_main_window(
    bot: Bot,
    state: FSMContext,
    fallback_message: Message,
    text: str,
    reply_markup: InlineKeyboardMarkup | None,
    preferred_target: tuple[int, int] | None,
) -> tuple[int, int]:
    target = preferred_target or await get_main_window(state)
    if target is not None and await _try_edit_message(bot, target[0], target[1], text, reply_markup):
        await set_main_window(state, *target)
        return target

    sent = await fallback_message.answer(text=text, reply_markup=reply_markup)
    rendered_to = _message_ref(sent)
    await set_main_window(state, *rendered_to)
    return rendered_to


async def render_main_window_from_message(
    message: Message,
    state: FSMContext,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> tuple[int, int]:
    return await _render_main_window(
        bot=message.bot,
        state=state,
        fallback_message=message,
        text=text,
        reply_markup=reply_markup,
        preferred_target=None,
    )


async def render_main_window_from_callback(
    callback: CallbackQuery,
    state: FSMContext,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> tuple[int, int]:
    source = _message_ref(callback.message)
    target = await get_main_window(state) or source
    rendered_to = await _render_main_window(
        bot=callback.bot,
        state=state,
        fallback_message=callback.message,
        text=text,
        reply_markup=reply_markup,
        preferred_target=target,
    )
    if source != rendered_to:
        await _try_clear_keyboard(callback.bot, source[0], source[1])
    return rendered_to
