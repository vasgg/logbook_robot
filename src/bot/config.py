from functools import cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from bot.enums import Stage

APP_NAME = "logbook"


def get_config_dict(prefix: str = "") -> SettingsConfigDict:
    return SettingsConfigDict(
        env_prefix=prefix,
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class Settings(BaseSettings):
    model_config = get_config_dict()

    bot_token: SecretStr
    bot_admin: int
    bot_stage: Stage = Stage.DEV
    db_path: Path = Path("data/logbook.db")
    sentry_dsn: str | None = None

    @property
    def db_url(self) -> str:
        return f"sqlite+aiosqlite:///{self.db_path}"


@cache
def get_settings() -> Settings:
    return Settings()
