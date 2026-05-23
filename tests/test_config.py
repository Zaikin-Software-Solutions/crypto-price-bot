from __future__ import annotations

import pytest
from pydantic import ValidationError

from crypto_price_bot.config import DEFAULT_COINS, Settings


def _base_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "-1001")
    monkeypatch.setenv("LIVECOINWATCH_API_KEY", "key")


def test_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    _base_env(monkeypatch)
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.coins == DEFAULT_COINS
    assert settings.publish_cron == "* * * * *"
    assert settings.log_level == "INFO"
    assert settings.log_format == "json"


def test_coins_parsed_from_csv(monkeypatch: pytest.MonkeyPatch) -> None:
    _base_env(monkeypatch)
    monkeypatch.setenv("COINS", "BTC, ETH ,TON")
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.coins == ("BTC", "ETH", "TON")


def test_missing_required_token_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "-1001")
    monkeypatch.setenv("LIVECOINWATCH_API_KEY", "key")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_timeout_must_be_positive(monkeypatch: pytest.MonkeyPatch) -> None:
    _base_env(monkeypatch)
    monkeypatch.setenv("HTTP_TIMEOUT_SECONDS", "0")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]
