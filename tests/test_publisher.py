from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from crypto_price_bot.adapters.livecoinwatch import LiveCoinWatchError
from crypto_price_bot.domain.models import CoinPrice, PriceSnapshot
from crypto_price_bot.services.publisher import PricePublisher


class _StubClient:
    def __init__(self, result: PriceSnapshot | Exception) -> None:
        self._result = result
        self.calls = 0

    async def fetch_prices(self, codes: tuple[str, ...]) -> PriceSnapshot:
        self.calls += 1
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


def _publisher(client: Any, bot: Any) -> PricePublisher:
    return PricePublisher(
        client=client,
        bot=bot,
        channel_id="-1001",
        coins=("BTC", "ETH"),
    )


@pytest.mark.asyncio
async def test_happy_path_sends_message() -> None:
    snap = PriceSnapshot(
        prices=(
            CoinPrice(code="BTC", rate_usd=65000),
            CoinPrice(code="ETH", rate_usd=3000),
        )
    )
    bot = AsyncMock()
    pub = _publisher(_StubClient(snap), bot)

    await pub.publish_once()

    bot.send_message.assert_awaited_once_with(
        chat_id="-1001",
        text="• BTC: $65000\n• ETH: $3000",
    )


@pytest.mark.asyncio
async def test_fetch_error_swallowed_and_nothing_sent() -> None:
    bot = AsyncMock()
    pub = _publisher(_StubClient(LiveCoinWatchError("boom")), bot)

    await pub.publish_once()

    bot.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_unexpected_exception_swallowed_and_nothing_sent() -> None:
    bot = AsyncMock()
    pub = _publisher(_StubClient(RuntimeError("net down")), bot)

    await pub.publish_once()

    bot.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_empty_snapshot_does_not_send() -> None:
    bot = AsyncMock()
    pub = _publisher(_StubClient(PriceSnapshot(prices=())), bot)

    await pub.publish_once()

    bot.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_telegram_failure_is_swallowed() -> None:
    snap = PriceSnapshot(prices=(CoinPrice(code="BTC", rate_usd=65000),))
    bot = AsyncMock()
    bot.send_message.side_effect = RuntimeError("tg 502")
    pub = _publisher(_StubClient(snap), bot)

    await pub.publish_once()  # must not raise

    bot.send_message.assert_awaited_once()
