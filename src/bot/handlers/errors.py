import logging

from aiogram import Router
from aiogram.types import ErrorEvent

logger = logging.getLogger(__name__)

router = Router()


@router.error()
async def error_handler(event: ErrorEvent) -> bool:
    """Handle all unhandled exceptions in handlers."""
    logger.exception(
        "Unhandled exception: %s",
        event.exception,
        exc_info=event.exception,
    )

    # Try to notify user
    update = event.update
    try:
        if update.message:
            await update.message.answer("Something went wrong. Try again later.")
        elif update.callback_query:
            await update.callback_query.answer("Something went wrong", show_alert=True)
    except Exception:
        logger.warning("Failed to send error message to user")

    # Return True to prevent further propagation
    return True
