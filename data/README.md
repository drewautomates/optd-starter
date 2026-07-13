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

## Where do you actually get tick data?

The most-asked, least-answered question in this whole corner of YouTube. You do **not** need a daily-bar source like Yahoo Finance — you need real intraday/tick data, or your fills are fiction (see `backtests/runs/run_fills_demo.py`).

| Source | What you get | Notes |
|--------|--------------|-------|
| **Databento** | Tick / 1-min historical for futures & equities | Free trial credit to start; clean, well-documented. Good first stop. |
| **Sierra Chart** | Native `.scid` tick files | If you already run SC for charting, you're sitting on the data. The desk reads these directly. |
| **Your broker's exports** | 1-min OHLCV CSV | Lowest barrier; drop into `tick/` and point `data.load_bars_csv` at it. |

> **The demo needs no data at all** — it generates synthetic random-walk sessions so the fills lesson is fully reproducible offline. Bring real data when you want to test a *real* idea.

> **On the live desk:** a private adapter reads native Sierra Chart `.scid` ticks through the same `load_bars()` interface the synthetic generator uses — so the identical pipeline runs on real fills. That adapter (and the data) stays private; the method here is the same.
