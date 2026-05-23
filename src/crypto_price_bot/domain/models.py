"""Domain models for cryptocurrency prices."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CoinPrice(BaseModel):
    """A single coin price in USD."""

    code: str = Field(min_length=1)
    rate_usd: float = Field(gt=0)


class PriceSnapshot(BaseModel):
    """A snapshot of prices for several coins fetched at the same time."""

    prices: tuple[CoinPrice, ...]

    def by_code(self, code: str) -> CoinPrice | None:
        for price in self.prices:
            if price.code == code:
                return price
        return None
