# OPTD Starter

A starter template for developing and backtesting trading systems with **Claude Code + TradingView**, the OPTD way: build the idea fast, sniff it on a chart, then validate it honestly.

This repo ships with a worked example — an **Opening Range Breakout (ORB)** indicator + strategy in Pine Script — and the one-shot prompt that builds them.

## The workflow (what the video walks through)

1. **Indicator** — see the setup on the chart (the eyes). `indicators/pine_reference/Opening_Range.pine`
2. **Strategy + TradingView Strategy Tester** — a quick "is there a pulse?" backtest. Fast, visual, *imperfect*. `indicators/pine_reference/Opening_Range_Strategy.pine`
3. **Python pipeline** 🚧 — the honest verdict: years of data, real fills, walk-forward, Monte-Carlo bust probability, permutation p-value. (`indicators/python/`, `backtests/`) — *stubbed out today; this layer fills in as I build the desk in public, starting with the deep-backtest video.*

Step 2 is something anyone can do. Step 3 is the differentiator: **rigorous vibe coding for trading** — and it fills in as I build in public, starting with the deep-backtest video.

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
│   ├── kernels.py         # validated exit kernels
│   └── runs/
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
3. To rebuild from scratch with Claude Code, hand it `research/prompts/orb_indicator_and_strategy.md`.

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
