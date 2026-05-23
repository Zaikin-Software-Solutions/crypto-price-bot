"""Entry point: wire everything together and run the scheduler."""

from __future__ import annotations

import asyncio
import signal

import aiohttp
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

from crypto_price_bot.adapters.livecoinwatch import LiveCoinWatchClient
from crypto_price_bot.config import Settings
from crypto_price_bot.logger import configure_logging, get_logger
from crypto_price_bot.scheduler import build_scheduler
from crypto_price_bot.services.publisher import PricePublisher


async def _run(settings: Settings) -> None:
    log = get_logger(__name__)
    log.info(
        "starting",
        coins=list(settings.coins),
        cron=settings.publish_cron,
        channel_id=settings.telegram_channel_id,
    )

    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=None),
    )
    http_session = aiohttp.ClientSession()
    try:
        client = LiveCoinWatchClient(
            api_key=settings.livecoinwatch_api_key,
            session=http_session,
            timeout_seconds=settings.http_timeout_seconds,
        )
        publisher = PricePublisher(
            client=client,
            bot=bot,
            channel_id=settings.telegram_channel_id,
            coins=settings.coins,
        )

        scheduler = build_scheduler(publisher.publish_once, settings.publish_cron)
        scheduler.start()

        stop = asyncio.Event()
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, stop.set)
            except NotImplementedError:
                # Windows / non-main thread: fall back to KeyboardInterrupt only.
                pass

        log.info("ready")
        await stop.wait()
        log.info("shutting_down")
        scheduler.shutdown(wait=False)
    finally:
        await http_session.close()
        await bot.session.close()


def main() -> None:
    settings = Settings()  # type: ignore[call-arg]  # values come from env / .env
    configure_logging(level=settings.log_level, fmt=settings.log_format)
    try:
        asyncio.run(_run(settings))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
