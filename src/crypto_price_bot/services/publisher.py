"""High-level publish flow: fetch prices → format → send to Telegram."""

from __future__ import annotations

from aiogram import Bot

from crypto_price_bot.adapters.livecoinwatch import LiveCoinWatchClient, LiveCoinWatchError
from crypto_price_bot.logger import get_logger
from crypto_price_bot.services.message_builder import build_message

log = get_logger(__name__)


class PricePublisher:
    """Orchestrates a single publish iteration."""

    def __init__(
        self,
        *,
        client: LiveCoinWatchClient,
        bot: Bot,
        channel_id: str,
        coins: tuple[str, ...],
    ) -> None:
        self._client = client
        self._bot = bot
        self._channel_id = channel_id
        self._coins = coins

    async def publish_once(self) -> None:
        try:
            snapshot = await self._client.fetch_prices(self._coins)
        except LiveCoinWatchError as exc:
            log.warning("livecoinwatch_unusable_response", error=str(exc))
            return
        except Exception:
            log.exception("livecoinwatch_fetch_failed")
            return

        message = build_message(snapshot, order=self._coins)
        if not message:
            log.warning("publish_skipped_empty_message", requested=list(self._coins))
            return

        try:
            await self._bot.send_message(chat_id=self._channel_id, text=message)
        except Exception:
            log.exception("telegram_send_failed", channel_id=self._channel_id)
            return

        log.info(
            "published",
            channel_id=self._channel_id,
            coins=[p.code for p in snapshot.prices],
        )
