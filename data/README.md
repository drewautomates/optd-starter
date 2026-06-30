# data/

Market data lives here. **Everything in `tick/` and `cache/` is gitignored** — never commit raw or cached data.

## Layout

| Folder | Contents |
|--------|----------|
| `tick/` | Raw tick / 1-minute exports (Sierra Chart `.scid`, broker CSV, etc.). |
| `cache/` | Parquet cache built from the raw data — fast to reload for backtests. |

## How to populate

1. Drop raw exports into `tick/` (e.g. a 1-minute OHLCV CSV per symbol, or `.scid` files).
2. Build the parquet cache into `cache/` with your loader (see `backtests/`).
3. Backtests read from `cache/` — keep the raw files around so the cache can be rebuilt.

> Keep symbols and timezones explicit. Note whether timestamps are UTC or exchange-local where you store them.
