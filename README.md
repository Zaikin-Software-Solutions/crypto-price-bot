# crypto-price-bot

[![CI](https://github.com/Zaikin-Software-Solutions/crypto-price-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/Zaikin-Software-Solutions/crypto-price-bot/actions/workflows/ci.yml)

A small Telegram bot that periodically publishes cryptocurrency prices to a channel.

Prices are fetched from [LiveCoinWatch](https://www.livecoinwatch.com/tools/api) and posted
on a cron schedule (every minute by default).

Public channel running this bot: [t.me/crypto_price_puls](https://t.me/crypto_price_puls).

---

## Features

- Async end-to-end: `aiohttp` for HTTP, `aiogram` 3.x for Telegram, `APScheduler` for cron.
- Coins matched by code, not by array index — adding/removing a coin won't shift other prices.
- Coins that the API doesn't return (or returns with a zero/invalid rate) are silently skipped
  in the published message rather than breaking the post.
- Structured logs via `structlog` (JSON in production, human-readable in dev).
- Config validated by `pydantic-settings`; required env vars fail fast at startup.
- Graceful shutdown on `SIGTERM` / `SIGINT`.
- Strict `mypy`, `ruff` lint + format, `pytest` test suite, GitHub Actions CI, multi-stage Docker.

## Quickstart

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- A Telegram bot token from [@BotFather](https://t.me/BotFather) and your channel id
- A LiveCoinWatch API key

### Local run

```bash
cp .env.example .env
# fill in TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, LIVECOINWATCH_API_KEY

uv sync --extra dev
uv run python -m crypto_price_bot
```

Or via Make:

```bash
make install
make run
```

### Docker

```bash
cp .env.example .env  # and fill it in
docker compose up -d --build
docker compose logs -f
```

## Configuration

All settings come from environment variables (a `.env` file is read in dev).

| Variable                | Required | Default              | Description                                              |
| ----------------------- | -------- | -------------------- | -------------------------------------------------------- |
| `TELEGRAM_BOT_TOKEN`    | yes      | —                    | Bot token from @BotFather.                               |
| `TELEGRAM_CHANNEL_ID`   | yes      | —                    | Channel id (e.g. `-1001234567890`) or `@channel`.        |
| `LIVECOINWATCH_API_KEY` | yes      | —                    | LiveCoinWatch API key.                                   |
| `COINS`                 | no       | `BTC,ETH,TON,KAS,_GRAM` | Comma-separated coin codes to publish, in order.      |
| `PUBLISH_CRON`          | no       | `* * * * *`          | Cron expression (UTC) for publish schedule.              |
| `HTTP_TIMEOUT_SECONDS`  | no       | `10`                 | Outgoing HTTP timeout for LiveCoinWatch.                 |
| `LOG_LEVEL`             | no       | `INFO`               | `DEBUG` / `INFO` / `WARNING` / `ERROR`.                  |
| `LOG_FORMAT`            | no       | `json`               | `json` (prod) or `console` (dev).                        |

## Project layout

```
src/crypto_price_bot/
  __main__.py            # entry point, wires everything together
  config.py              # pydantic-settings
  logger.py              # structlog config
  scheduler.py           # APScheduler wiring
  domain/models.py       # CoinPrice, PriceSnapshot
  adapters/
    livecoinwatch.py     # HTTP client for the prices API
  services/
    message_builder.py   # snapshot → Telegram text
    publisher.py         # fetch → format → send orchestration
tests/                   # pytest, mocks via aioresponses
```

The architecture is intentionally layered:

- **domain** has no I/O and no dependencies on other layers.
- **adapters** wrap external services (HTTP APIs, Telegram).
- **services** combine domain + adapters into use cases.
- **`__main__`** is the only place that knows how to build everything.

## Development

```bash
make install     # uv sync --extra dev
make check       # ruff + mypy + pytest
make test
make lint
make format
make typecheck
```

CI runs the same checks on every push and PR, plus a Docker build.

## License

MIT — see [LICENSE](./LICENSE).
