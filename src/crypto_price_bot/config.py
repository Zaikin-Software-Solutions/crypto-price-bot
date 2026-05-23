"""Application configuration loaded from environment variables."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_COINS: tuple[str, ...] = ("BTC", "ETH", "TON", "KAS", "_GRAM")


def _parse_coins(raw: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in raw.split(",") if part.strip())


class Settings(BaseSettings):
    """Runtime configuration.

    All values are loaded from environment variables (or a local .env file in dev).
    Names mirror those documented in .env.example.
    """

    telegram_bot_token: str = Field(min_length=1)
    telegram_channel_id: str = Field(min_length=1)
    livecoinwatch_api_key: str = Field(min_length=1)

    coins_raw: str = Field(default=",".join(DEFAULT_COINS), alias="COINS")
    publish_cron: str = "* * * * *"
    http_timeout_seconds: float = Field(default=10.0, gt=0, le=60)

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "console"] = "json"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def coins(self) -> tuple[str, ...]:
        parsed = _parse_coins(self.coins_raw)
        return parsed or DEFAULT_COINS
