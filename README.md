# OPTD Starter

A starter template for developing and backtesting trading systems with **Claude Code**, the OPTD way: build the idea fast on **TradingView**, sniff it on a chart, then validate it honestly on **Sierra Chart** tick data.

This repo ships with a worked example — an **Opening Range Breakout (ORB)** indicator + strategy in Pine Script — and the one-shot prompt that builds them.

## The workflow (what the video walks through)

1. **Indicator** — see the setup on the chart (the eyes). `indicators/pine_reference/Opening_Range.pine`
2. **Strategy + TradingView Strategy Tester** — a quick "is there a pulse?" backtest. Fast, visual, *imperfect*. `indicators/pine_reference/Opening_Range_Strategy.pine`
3. **Python pipeline** — the honest verdict. **The first layer is in: honest fills.** A backtest can manufacture a fake edge out of *nothing* just by assuming fills it never got. Run it yourself:

   ```bash
   python backtests/runs/run_fills_demo.py
   ```

   It runs the same ORB through two fill models on **random-walk data** (which has no real edge). The honest fills report ~0, as they must. The naive fills conjure a positive expectancy from thin air — that gap is the lie. Files: `indicators/python/orb.py`, `backtests/fills.py`, `backtests/kernels.py`. More gates (walk-forward, permutation, Monte-Carlo) fill in as I build the desk in public.

4. **Sierra Chart tick data — where honest fills come from.** A backtest is only as honest as its data, and the honest-fills lesson turns on one bit per bar — *did the high print before the low?* — that lives in the **ticks**, not in OHLC. This slice is a teaching Sierra Chart `.scid` reader: it writes a synthetic tick stream in the real `.scid` record shape, reads it back by parsing the bytes (the actual skill), and reconstructs bars from the ticks — then feeds those tick-rebuilt bars straight into the honest-vs-naive test. Run it:

   ```bash
   python backtests/runs/run_scid_demo.py
   ```

   Same random-walk data (honest ≈ 0), but now the whole thing is anchored on the tick reading that makes honest fills possible in the first place. Once you can read the ticks, you reconstruct any strategy tick by tick instead of trusting a platform's guess. Files: `backtests/ticks.py`, `backtests/runs/run_scid_demo.py`.

Step 2 is something anyone can do. Steps 3–4 are the differentiator: **rigorous vibe coding for trading**.

> **Teaching layer vs production.** What's in this repo is the *teaching* layer — the method, on synthetic data, so you can see the lie with zero hand-waving. The `.scid` reader here parses the real record format but runs on a synthetic tick file. The *production* harness — the real `.scid` reader over live exchange files (timezone handling + a parquet cache that replays years in seconds so you can run thousands of permutations), the multi-gate validated kernel, and the full validation gauntlet — runs on the live desk and ships in the [community](https://onepersontradedesk.com). **The methodology is free; the working files are the paid part. No methodology is ever gated.**

## Structure

```
optd-starter/
├── CLAUDE.md              # project context for Claude Code
├── .claude/
│   ├── settings.json      # tool permissions
│   └── agents/            # sub-agents (added as the desk grows)
├── data/
│   ├── tick/              # raw tick data (gitignored)
│   ├── cache/             # parquet cache (gitignored)
│   └── README.md          # how to populate
├── research/
│   ├── prompts/           # prompt library (one-shot builders)
│   └── notebooks/
├── backtests/
│   ├── data.py            # Bar + synthetic sessions + CSV loader
│   ├── fills.py           # fill models — naive (the lie) vs honest
│   ├── kernels.py         # validated exit kernels + self-test
│   ├── ticks.py           # teaching .scid reader (ticks → bars)
│   └── runs/              # runnable demos (run_*.py)
├── indicators/
│   ├── python/            # Python implementations (parity with Pine)
│   └── pine_reference/    # Pine source — the spec
├── sierra/
│   ├── studies/           # .cpp ACSIL studies
│   └── exports/
├── journal/
│   └── schema.sql
└── README.md
```

## How this maps to the desk (the 10 roles)

This repo is the tangible companion to the [One Person Trade Desk](https://onepersontradedesk.com) tour — the same roles, as folders. The judgment role (Portfolio Manager) is *you*; **Claude Code is the bench** that runs the rest.

| Folder | Desk role |
|--------|-----------|
| `research/` | **Quant Researcher** — ideas → specs, the prompt library |
| `indicators/` | **Quant Developer** — Claude Code writes the code (Pine = spec, Python = parity) |
| `backtests/` | **Quant Researcher + Risk Manager** — exit kernels, walk-forward, Monte-Carlo |
| `data/` | **Data Engineering** — tick data + parquet cache |
| `sierra/` | **Execution Trader + Tech Infrastructure** — ACSIL studies, live exports |
| `journal/` | **Performance Analytics + Compliance** — trade log + honest self-review |

Most of these are scaffolded today and fill in as I build each role on camera.

## Quick start

1. Open `indicators/pine_reference/Opening_Range.pine` and `Opening_Range_Strategy.pine`, paste into TradingView's Pine Editor, add to chart.
2. Use an **intraday** chart (1m–15m) on a futures symbol (`NQ1!`, `ES1!`, `MNQ1!`). Chart TF ≤ Signal TF.
3. Run the Python demos (Python 3.9+, `pip install -r requirements.txt` — it's just numpy):
   `python backtests/runs/run_fills_demo.py` and `python backtests/runs/run_scid_demo.py`. No market data needed — both generate synthetic sessions.
4. To rebuild from scratch with Claude Code, hand it `research/prompts/orb_indicator_and_strategy.md`.

## Hard-won gotchas (baked into the prompt)

- **Range from high/low, never closes** — close-based collapses to a zero-width line when the OR window is a single signal-TF bar.
- **Levels computed inline, not through `request.security`** — the OR high/low are timeframe-invariant, so computing them inline draws smoothly and makes the indicator and strategy match exactly. Pulling levels through `request.security` causes a zero-width "snap"/immediate-drop and indicator-vs-strategy drift.
- **Only the consecutive-close counter is timeframe-dependent** — it runs on a fixed Signal timeframe via `request.security`, so swapping the chart view doesn't move the entries.
- **Return counts, not momentary booleans, across `request.security`** — momentary `true` flags don't survive the security boundary; detect the breakout edge on the chart side.
- **Futures need `margin_long/short`** in the `strategy()` call — the default (0) demands full notional (~$600k for 1 NQ), so a $50k account silently places zero trades ("This report requires trade data").

## Follow along

This repo fills in as I build the desk in public. The **[newsletter](https://onepersontradedesk.com/subscribe)** is where it connects — new drops, the methodology behind them, and the waitlist for the OPTD community when it opens.

**Coming next:** the **backtest bias-reviewer** — the Claude skill that catches lookahead, overfitting, and survivorship bias before you trust a curve. It ships with the next video; subscribe to get it first.

→ **[Subscribe](https://onepersontradedesk.com/subscribe)** · [onepersontradedesk.com](https://onepersontradedesk.com)

## License

MIT — see [LICENSE](LICENSE). Educational/research only; **not financial advice**.
