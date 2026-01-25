import asyncio
import logging
from contextlib import suppress

import sentry_sdk
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import APP_NAME, get_settings
from bot.enums import Stage
from bot.handlers.callbacks import router as callbacks_router
from bot.handlers.errors import router as errors_router
from bot.handlers.start import router as start_router
from bot.internal.logging_config import setup_logging
from bot.internal.notify import on_shutdown, on_startup
from bot.middlewares.auth import AuthMiddleware
from bot.middlewares.logging import LoggingMiddleware
from bot.middlewares.session import DbSessionMiddleware
from bot.middlewares.updates_dumper import UpdatesDumperMiddleware
from database.db import get_engine, get_session_factory
from database.models import Base

logger = logging.getLogger(__name__)


def setup_sentry(dsn: str | None, stage: Stage) -> None:
    if stage != Stage.PROD:
        logger.info("Sentry disabled in %s mode", stage.value)
        return

    if not dsn:
        logger.warning("Sentry DSN not configured")
        return

    sentry_sdk.init(
        dsn=dsn,
        environment=stage.value,
        traces_sample_rate=0.1,
        send_default_pii=False,
    )
    logger.info("Sentry initialized")


async def init_db(engine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def main() -> None:
    setup_logging(APP_NAME)
    settings = get_settings()

    setup_sentry(settings.sentry_dsn, settings.bot_stage)

    settings.db_path.parent.mkdir(parents=True, exist_ok=True)

    engine = get_engine()
    session_factory = get_session_factory(engine)

    await init_db(engine)

    bot = Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.startup.register(lambda: on_startup(bot, settings))
    dp.shutdown.register(lambda: on_shutdown(bot, settings))

    # Outer middleware (runs first)
    dp.update.outer_middleware(UpdatesDumperMiddleware())

    # Inner middlewares
    dp.message.middleware(DbSessionMiddleware(session_factory))
    dp.callback_query.middleware(DbSessionMiddleware(session_factory))
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())

    dp.include_router(errors_router)
    dp.include_router(start_router)
    dp.include_router(callbacks_router)

    logger.info("Starting bot in %s mode", settings.bot_stage.value)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await engine.dispose()
        logger.info("Bot stopped gracefully")


def run_main() -> None:
    with suppress(KeyboardInterrupt, SystemExit):
        asyncio.run(main())


if __name__ == "__main__":
    run_main()
