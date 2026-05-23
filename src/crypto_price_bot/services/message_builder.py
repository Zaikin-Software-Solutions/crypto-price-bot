"""Format a Telegram message from a price snapshot."""

from __future__ import annotations

from collections.abc import Mapping

from crypto_price_bot.domain.models import PriceSnapshot

# How to render each coin: (display label, decimal places).
# Codes missing from the snapshot are silently skipped so partial data still publishes.
DEFAULT_FORMATS: Mapping[str, tuple[str, int]] = {
    "BTC": ("BTC", 0),
    "ETH": ("ETH", 0),
    "TON": ("TON", 1),
    "KAS": ("KSP", 4),
    "_GRAM": ("GRAM", 3),
    "CAS": ("CAS", 4),
}


def build_message(
    snapshot: PriceSnapshot,
    *,
    order: tuple[str, ...] = ("BTC", "ETH", "TON", "KAS", "_GRAM"),
    formats: Mapping[str, tuple[str, int]] = DEFAULT_FORMATS,
) -> str:
    """Build the Telegram message body.

    Coins are rendered in ``order``. Any coin missing from the snapshot is skipped.
    Returns an empty string if no coins are available — callers should treat that
    as "nothing to publish".
    """

    lines: list[str] = []
    for code in order:
        price = snapshot.by_code(code)
        if price is None:
            continue
        label, decimals = formats.get(code, (code, 2))
        value = _format_rate(price.rate_usd, decimals)
        lines.append(f"• {label}: ${value}")
    return "\n".join(lines)


def _format_rate(rate: float, decimals: int) -> str:
    if decimals <= 0:
        return f"{round(rate)}"
    return f"{round(rate, decimals)}"
