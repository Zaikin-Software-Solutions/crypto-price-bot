from __future__ import annotations

import aiohttp
import pytest
from aioresponses import aioresponses

from crypto_price_bot.adapters.livecoinwatch import (
    API_URL,
    LiveCoinWatchClient,
    LiveCoinWatchError,
)


@pytest.fixture
async def session() -> aiohttp.ClientSession:  # type: ignore[misc]
    s = aiohttp.ClientSession()
    try:
        yield s
    finally:
        await s.close()


async def test_parses_prices_by_code_regardless_of_order(
    session: aiohttp.ClientSession,
) -> None:
    payload = [
        {"code": "TON", "rate": 5.27},
        {"code": "BTC", "rate": 65000.4},
        {"code": "ETH", "rate": 3000.5},
    ]
    with aioresponses() as m:
        m.post(API_URL, payload=payload)
        client = LiveCoinWatchClient(api_key="k", session=session)
        snap = await client.fetch_prices(("BTC", "ETH", "TON"))

    assert snap.by_code("BTC") is not None
    assert snap.by_code("BTC").rate_usd == 65000.4  # type: ignore[union-attr]
    assert snap.by_code("ETH").rate_usd == 3000.5  # type: ignore[union-attr]
    assert snap.by_code("TON").rate_usd == 5.27  # type: ignore[union-attr]


async def test_missing_coins_are_dropped(session: aiohttp.ClientSession) -> None:
    payload = [
        {"code": "BTC", "rate": 65000.4},
        # ETH absent
    ]
    with aioresponses() as m:
        m.post(API_URL, payload=payload)
        client = LiveCoinWatchClient(api_key="k", session=session)
        snap = await client.fetch_prices(("BTC", "ETH"))

    assert {p.code for p in snap.prices} == {"BTC"}


async def test_zero_or_missing_rate_is_dropped(session: aiohttp.ClientSession) -> None:
    payload = [
        {"code": "BTC", "rate": 65000.4},
        {"code": "ETH", "rate": 0},
        {"code": "TON", "rate": None},
        {"code": "KAS"},
    ]
    with aioresponses() as m:
        m.post(API_URL, payload=payload)
        client = LiveCoinWatchClient(api_key="k", session=session)
        snap = await client.fetch_prices(("BTC", "ETH", "TON", "KAS"))

    assert {p.code for p in snap.prices} == {"BTC"}


async def test_all_missing_raises(session: aiohttp.ClientSession) -> None:
    with aioresponses() as m:
        m.post(API_URL, payload=[])
        client = LiveCoinWatchClient(api_key="k", session=session)
        with pytest.raises(LiveCoinWatchError):
            await client.fetch_prices(("BTC",))


async def test_non_200_raises(session: aiohttp.ClientSession) -> None:
    with aioresponses() as m:
        m.post(API_URL, status=500, body="boom")
        client = LiveCoinWatchClient(api_key="k", session=session)
        with pytest.raises(LiveCoinWatchError):
            await client.fetch_prices(("BTC",))


async def test_unexpected_shape_raises(session: aiohttp.ClientSession) -> None:
    with aioresponses() as m:
        m.post(API_URL, payload={"error": "nope"})
        client = LiveCoinWatchClient(api_key="k", session=session)
        with pytest.raises(LiveCoinWatchError):
            await client.fetch_prices(("BTC",))
