"""LiveCoinWatch HTTP adapter.

Docs: https://livecoinwatch.github.io/lcw-api-docs/?python#coinslist
"""

from __future__ import annotations

from typing import Any

import aiohttp

from crypto_price_bot.domain.models import CoinPrice, PriceSnapshot

API_URL = "https://api.livecoinwatch.com/coins/map"


class LiveCoinWatchError(RuntimeError):
    """Raised when LiveCoinWatch returns an unusable response."""


class LiveCoinWatchClient:
    """Thin async client for the /coins/map endpoint."""

    def __init__(
        self,
        api_key: str,
        session: aiohttp.ClientSession,
        *,
        timeout_seconds: float = 10.0,
        api_url: str = API_URL,
    ) -> None:
        self._api_key = api_key
        self._session = session
        self._timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self._api_url = api_url

    async def fetch_prices(self, codes: tuple[str, ...]) -> PriceSnapshot:
        """Fetch USD prices for the given coin codes.

        Order of prices in the response is not assumed: prices are matched by ``code``.
        """

        payload = {
            "codes": list(codes),
            "currency": "USD",
            "sort": "age",
            "order": "descending",
        }
        headers = {
            "content-type": "application/json",
            "x-api-key": self._api_key,
        }

        async with self._session.post(
            self._api_url,
            json=payload,
            headers=headers,
            timeout=self._timeout,
        ) as response:
            if response.status != 200:
                body = await response.text()
                raise LiveCoinWatchError(
                    f"LiveCoinWatch returned HTTP {response.status}: {body[:200]}"
                )
            data = await response.json()

        return _parse_response(data, requested=codes)


def _parse_response(data: Any, *, requested: tuple[str, ...]) -> PriceSnapshot:
    if not isinstance(data, list):
        raise LiveCoinWatchError(f"Expected a list, got {type(data).__name__}")

    prices: list[CoinPrice] = []
    by_code: dict[str, dict[str, Any]] = {}
    for item in data:
        if not isinstance(item, dict):
            continue
        code = item.get("code")
        if isinstance(code, str):
            by_code[code] = item

    for code in requested:
        item = by_code.get(code)
        if item is None:
            continue
        rate = item.get("rate")
        if not isinstance(rate, (int, float)) or rate <= 0:
            continue
        prices.append(CoinPrice(code=code, rate_usd=float(rate)))

    if not prices:
        raise LiveCoinWatchError(f"No usable prices in response for codes {list(requested)}")

    return PriceSnapshot(prices=tuple(prices))
