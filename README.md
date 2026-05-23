# crypto-price-bot

[![CI](https://github.com/Zaikin-Software-Solutions/crypto-price-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/Zaikin-Software-Solutions/crypto-price-bot/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/Zaikin-Software-Solutions/crypto-price-bot?display_name=tag&sort=semver&cacheSeconds=300)](https://github.com/Zaikin-Software-Solutions/crypto-price-bot/releases)
[![Docker image](https://img.shields.io/badge/ghcr.io-crypto--price--bot-blue?logo=docker&logoColor=white)](https://github.com/Zaikin-Software-Solutions/crypto-price-bot/pkgs/container/crypto-price-bot)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)

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

## Prerequisites (all install methods)

- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- The numeric id of a Telegram channel where the bot is admin (e.g. `-1001234567890`)
- A free LiveCoinWatch API key from <https://www.livecoinwatch.com/tools/api>

## Install

### A. Prebuilt image from GHCR (recommended for servers)

CI publishes a multi-arch (`linux/amd64` + `linux/arm64`) image to
`ghcr.io/zaikin-software-solutions/crypto-price-bot` on every push to `main`
and on every `vX.Y.Z` git tag — nothing to build on your side.

Requires only Docker + Docker Compose.

```bash
mkdir -p /opt/crypto-price-bot && cd /opt/crypto-price-bot

# Pull the published compose file and the example env template.
curl -sSL https://raw.githubusercontent.com/Zaikin-Software-Solutions/crypto-price-bot/main/docker-compose.yml -o docker-compose.yml
curl -sSL https://raw.githubusercontent.com/Zaikin-Software-Solutions/crypto-price-bot/main/.env.example -o .env

# Edit .env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, LIVECOINWATCH_API_KEY are required.
$EDITOR .env

docker compose pull
docker compose up -d
docker compose logs -f
```

Pin to a specific version by replacing `:latest` in `docker-compose.yml` with
`:1.0.0` (or `:1` / `:1.0` for floating major / minor). To update later:
`docker compose pull && docker compose up -d`.

### B. Build with Docker from sources (for local development)

Requires Docker + Docker Compose + `git`.

```bash
git clone https://github.com/Zaikin-Software-Solutions/crypto-price-bot.git
cd crypto-price-bot
cp .env.example .env  # then fill it in
docker compose -f docker-compose.yml -f docker-compose.build.yml up -d --build
docker compose logs -f
```

### C. Run directly with Python (no Docker)

Requires Python 3.12+ and [`uv`](https://docs.astral.sh/uv/)
(`curl -LsSf https://astral.sh/uv/install.sh | sh`).

```bash
git clone https://github.com/Zaikin-Software-Solutions/crypto-price-bot.git
cd crypto-price-bot
cp .env.example .env  # then fill it in
uv sync --extra dev
uv run python -m crypto_price_bot
```

Or via Make: `make install && make run`.

## Configuration

All settings come from environment variables (a `.env` file is read in dev).

| Variable                | Required | Default              | Description                                              |
| ----------------------- | -------- | -------------------- | -------------------------------------------------------- |
| `TELEGRAM_BOT_TOKEN`    | yes      | —                    | Bot token from @BotFather.                               |
| `TELEGRAM_CHANNEL_ID`   | yes      | —                    | Channel id (e.g. `-1001234567890`) or `@channel`.        |
| `LIVECOINWATCH_API_KEY` | yes      | —                    | LiveCoinWatch API key.                                   |
| `COINS`                 | no       | `BTC,ETH,TONCOIN,KAS,_GRAM` | Comma-separated LiveCoinWatch coin codes to publish, in order. (LCW uses `TONCOIN`, not `TON`.) |
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
