from __future__ import annotations

from crypto_price_bot.domain.models import CoinPrice, PriceSnapshot
from crypto_price_bot.services.message_builder import build_message


def _snapshot(items: dict[str, float]) -> PriceSnapshot:
    return PriceSnapshot(prices=tuple(CoinPrice(code=c, rate_usd=r) for c, r in items.items()))


def test_renders_in_requested_order() -> None:
    snap = _snapshot({"ETH": 3000.5, "BTC": 65000.4, "TONCOIN": 5.27})
    msg = build_message(snap, order=("BTC", "ETH", "TONCOIN"))
    assert msg == "• BTC: $65000\n• ETH: $3000\n• TON: $5.27"


def test_missing_coins_are_skipped_silently() -> None:
    snap = _snapshot({"BTC": 65000.0, "TONCOIN": 5.27})
    msg = build_message(snap, order=("BTC", "ETH", "TONCOIN", "KAS"))
    assert msg == "• BTC: $65000\n• TON: $5.27"


def test_empty_snapshot_returns_empty_string() -> None:
    snap = PriceSnapshot(prices=())
    assert build_message(snap, order=("BTC",)) == ""


def test_unknown_code_uses_two_decimals_by_default() -> None:
    snap = _snapshot({"XYZ": 1.23456})
    msg = build_message(snap, order=("XYZ",))
    assert msg == "• XYZ: $1.23"


def test_decimals_zero_rounds_to_int() -> None:
    snap = _snapshot({"BTC": 65000.49})
    msg = build_message(snap, order=("BTC",))
    assert msg == "• BTC: $65000"


def test_kaspa_label_renamed_to_ksp() -> None:
    snap = _snapshot({"KAS": 0.12345})
    msg = build_message(snap, order=("KAS",))
    assert msg == "• KSP: $0.1235"
