# OPTD Starter

A starter template for developing and backtesting trading systems with **Claude Code**, the OPTD way: build the idea fast on **TradingView**, sniff it on a chart, then validate it honestly on **Sierra Chart** tick data.

This repo ships with a worked example — an **Opening Range Breakout (ORB)** indicator + strategy in Pine Script — and the one-shot prompt that builds them.

[📺 **The videos**](https://www.youtube.com/channel/UCTN36flT82vfS-2sw1QBu9w) · [📧 **Newsletter**](https://onepersontradedesk.com/subscribe) · [🌐 **onepersontradedesk.com**](https://onepersontradedesk.com)

## The library — one component per video

Every video adds a runnable component to this repo. This table is the index, newest first. The method is always in the video, free.

| # | Video | What it shipped here |
|---|---|---|
| 5 | [How to Build a Sierra Chart Indicator with Claude Code](https://youtu.be/9l_DITJmeQI) | The ACSIL signal study ([`sierra/studies/OPTD_Opening_Range.cpp`](sierra/studies/OPTD_Opening_Range.cpp)), the deploy scripts + four build gotchas ([`sierra/DEPLOY.md`](sierra/DEPLOY.md)), the chartbook ([`sierra/chartbooks/OPTD.Cht`](sierra/chartbooks/OPTD.Cht)), and the one-shot study prompt ([`research/prompts/orb_sierra_chart_study.md`](research/prompts/orb_sierra_chart_study.md)) |
| 4 | [Claude Code Trading Strategies Are Easy to Build. That's the Problem. (I Tested 5)](https://youtu.be/WdPdJCU88-U) | The three-test gauntlet — **FIT** ([`run_cheat_demo.py`](backtests/runs/run_cheat_demo.py)), **FILL** ([`run_fills_demo.py`](backtests/runs/run_fills_demo.py)), **FLUKE** ([`run_drift_demo.py`](backtests/runs/run_drift_demo.py)), end to end ([`run_gauntlet.py`](backtests/runs/run_gauntlet.py)) |
| 3 | [Claude Code Backtests on Real Tick Data (The Test TradingView Can't Run)](https://youtu.be/zxrtVFJyujQ) | The teaching Sierra Chart `.scid` tick reader ([`backtests/ticks.py`](backtests/ticks.py)) and the ticks → bars → honest-fills demo ([`run_scid_demo.py`](backtests/runs/run_scid_demo.py)) |
| 2 | [Hedge Funds Pay $5M for This Trading Desk. I Built Mine for $150 a Month](https://youtu.be/L3xhBOKvrO8) | The desk itself — this repo's folders mirror the [10 desk roles](#how-this-maps-to-the-desk-the-10-roles) that video tours |
| 1 | [Opening Range Breakout Strategy Doesn't Work (Claude Code Backtest)](https://youtu.be/n8-SYGHzuHs) | The worked example — ORB indicator + strategy in Pine ([`indicators/pine_reference/`](indicators/pine_reference)) and the prompt that builds them ([`research/prompts/orb_indicator_and_strategy.md`](research/prompts/orb_indicator_and_strategy.md)) |

⭐ **Star the repo to follow along** — a new row lands with every video, and stars are how other traders find this.

## Quick start (60 seconds, no market data)

```bash
git clone https://github.com/drewautomates/optd-starter.git
cd optd-starter
python3 -m pip install -r requirements.txt      # just numpy
python3 backtests/runs/run_gauntlet.py
```

That runs all three bias tests end to end in a few seconds. **Nothing to download, no API key, no broker account** — every demo generates its own synthetic data, so it runs the same on Windows, macOS, and Linux, offline. Requires **Python 3.9+**.

> **Windows:** use `python` instead of `python3` (or `py -3`). macOS and most Linux distros ship only `python3` — that's the one difference in every command on this page. Run from the repo root; no virtualenv or `PYTHONPATH` setup is needed, though a venv is never a bad idea.

Then, for the TradingView side:

1. Paste `indicators/pine_reference/Opening_Range.pine` and `Opening_Range_Strategy.pine` into TradingView's Pine Editor, add to chart.
2. Use an **intraday** chart (1m–15m) on a futures symbol (`NQ1!`, `ES1!`, `MNQ1!`). Chart TF ≤ Signal TF.
3. To rebuild the Pine from scratch with Claude Code, hand it `research/prompts/orb_indicator_and_strategy.md`.

## The workflow (what the video walks through)

1. **Indicator** — see the setup on the chart (the eyes). `indicators/pine_reference/Opening_Range.pine`
2. **Strategy + TradingView Strategy Tester** — a quick "is there a pulse?" backtest. Fast, visual, *imperfect*. `indicators/pine_reference/Opening_Range_Strategy.pine`
3. **Python pipeline** — the honest verdict. **The first layer is in: honest fills.** A backtest can manufacture a fake edge out of *nothing* just by assuming fills it never got. Run it yourself:

   ```bash
   python3 backtests/runs/run_fills_demo.py
   ```

   It runs the same ORB through two fill models on **random-walk data** (which has no real edge). The honest fills report ~0, as they must. The naive fills conjure a positive expectancy from thin air — that gap is the lie. Files: `indicators/python/orb.py`, `backtests/fills.py`, `backtests/kernels.py`. More gates (walk-forward, permutation, Monte-Carlo) fill in as I build the desk in public.

4. **Sierra Chart tick data — where honest fills come from.** A backtest is only as honest as its data, and the honest-fills lesson turns on one bit per bar — *did the high print before the low?* — that lives in the **ticks**, not in OHLC. This slice is a teaching Sierra Chart `.scid` reader: it writes a synthetic tick stream in the real `.scid` record shape, reads it back by parsing the bytes (the actual skill), and reconstructs bars from the ticks — then feeds those tick-rebuilt bars straight into the honest-vs-naive test. Run it:

   ```bash
   python3 backtests/runs/run_scid_demo.py
   ```

   Same random-walk data (honest ≈ 0), but now the whole thing is anchored on the tick reading that makes honest fills possible in the first place. Once you can read the ticks, you reconstruct any strategy tick by tick instead of trusting a platform's guess. Files: `backtests/ticks.py`, `backtests/runs/run_scid_demo.py`.

Step 2 is something anyone can do. Steps 3–4 are the differentiator: **rigorous vibe coding for trading**.

## The gauntlet — three tests, free, runnable today

Every backtest tells you three lies. Each one has a test, all three are in this repo, and they run on
synthetic random-walk data on purpose: **random data has no edge in it**, so every dollar these tests
report as profit is provably fake. You watch each bias manufacture money and then hand it back — the
lie, in a lab, where you can see all of it. Then you point them at your own results.

| Test | Command | What it catches |
|---|---|---|
| **1 · FIT** | `python3 backtests/runs/run_cheat_demo.py` | Let the backtest cheat — signal-close entries, no commission, fill on every touch — then take the cheats away one at a time. If it still loses at pass 0, you're done; nothing else needs checking. |
| **2 · FILL** | `python3 backtests/runs/run_fills_demo.py` | When your stop and your target land inside the same bar, which one hit first? The bar doesn't record it. Naive fills guess in your favour; honest fills don't. |
| **3 · FLUKE** | `python3 backtests/runs/run_drift_demo.py` | Take the signal away. Same times in, same times out, no signal — just be in the market. Run in a flat market and a rising one, because this test only bites in one of them. |
| **all three** | `python3 backtests/runs/run_gauntlet.py` | End to end in a few seconds. |

Run them before you put money behind a strategy, not after.

Test three reports every gap against its own **noise floor**. The strategy and its control
trade the same bars, so they're scored as a paired difference — the market's variance cancels
and what's left is the part the signal is answerable for. A gap smaller than that floor comes
back **INCONCLUSIVE**, not as a win. That one rule disqualifies more strategies than the three
tests do, and it's the reason the flat-market run below refuses to call a +$0.83/trade result
an edge.

> **Teaching layer vs production.** What's in this repo is the *teaching* layer — the method, on synthetic data, so you can see the lie with zero hand-waving. The `.scid` reader here parses the real record format but runs on a synthetic tick file. The *production* harness — the real `.scid` reader over live exchange files (timezone handling + a parquet cache that replays years in seconds so you can run thousands of permutations), the multi-gate validated kernel, and the *production* gauntlet running these same three tests over real exchange data — runs on the live desk and ships in the [community](https://onepersontradedesk.com). **The three tests above are free and always will be. What's paid is the data and the engine, never the method. No methodology is ever gated.**

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
│   ├── data.py            # Bar + synthetic sessions (optional drift) + CSV loader
│   ├── costs.py           # commission + slippage presets — the cheat ladder  (test 1)
│   ├── fills.py           # fill models — naive (the lie) vs honest            (test 2)
│   ├── drift.py           # the no-signal control + the noise floor            (test 3)
│   ├── kernels.py         # validated exit kernels + self-test
│   ├── ticks.py           # teaching .scid reader (ticks → bars)
│   └── runs/              # runnable demos
│       ├── run_gauntlet.py    # all three bias tests
│       ├── run_cheat_demo.py  # 1 · FIT
│       ├── run_fills_demo.py  # 2 · FILL
│       ├── run_drift_demo.py  # 3 · FLUKE
│       └── run_scid_demo.py   # ticks → bars → honest fills
├── indicators/
│   ├── python/            # Python implementations (parity with Pine)
│   └── pine_reference/    # Pine source — the spec
├── sierra/
│   ├── DEPLOY.md          # deploy → build → verify, and the four gotchas
│   ├── scripts/           # deploy.ps1 / deploy.sh → your ACS_Source
│   ├── studies/           # .cpp ACSIL studies
│   ├── chartbooks/        # .Cht chartbooks
│   └── exports/           # Export Chart Data CSVs
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
| `sierra/` | **Execution Trader + Tech Infrastructure** — ACSIL studies, live exports. Start at [`sierra/DEPLOY.md`](sierra/DEPLOY.md). |
| `journal/` | **Performance Analytics + Compliance** — trade log + honest self-review |

Most of these are scaffolded today and fill in as I build each role on camera.

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
