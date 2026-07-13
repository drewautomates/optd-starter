# CLAUDE.md — OPTD Starter

Context for Claude Code working in this repo.

## What this is

A starter template for building and backtesting trading systems with Claude Code + TradingView + Sierra Chart. The flagship example is an **Opening Range Breakout (ORB)** in Pine Script (indicator + strategy). The Python layer is live: a parity ORB (`indicators/python/orb.py`), the honest-fills kernel (`backtests/`), and a teaching Sierra Chart `.scid` tick reader (`backtests/ticks.py`). Deeper validation gates (walk-forward, permutation, Monte-Carlo) fill in as I build the desk in public.

Author/brand: **OPTD**. Tone: engineering + honesty + earned intuition. "Honest ___" is the house qualifier.

## Where things go

| Path | Purpose |
|------|---------|
| `indicators/pine_reference/` | Pine Script — the **spec**. The source of truth for any logic. |
| `indicators/python/` | Python reimplementations that must stay in **parity** with the Pine. |
| `backtests/data.py` | `Bar` (with `up_first`, the intrabar truth) + synthetic sessions + CSV loader. |
| `backtests/fills.py` | Fill models — naive (the lie) vs honest. |
| `backtests/kernels.py` | Validated exit kernels (entry → stop/target → exit price/R) + `validate_kernels()` self-test. |
| `backtests/ticks.py` | Teaching `.scid` reader — parse ticks, rebuild bars, derive `up_first`. |
| `backtests/runs/` | Runnable demos (`run_*.py`, tracked); saved outputs (gitignored). |
| `research/prompts/` | One-shot prompt library — paste into Claude Code to (re)generate artifacts. |
| `research/notebooks/` | Exploratory analysis. |
| `data/tick/`, `data/cache/` | Raw + cached market data. **Gitignored.** See `data/README.md`. |
| `sierra/studies/` | Sierra Chart ACSIL (C++) studies. |
| `journal/schema.sql` | Trade journal DB schema. |

## Conventions

- **Pine is the spec.** When Pine and Python disagree, Pine wins (or you fix both in the same change). Note parity in commits.
- **Pine Script v6.** Author tag `OPTD`.
- **Honest backtesting.** The TradingView Strategy Tester is a first sniff, not proof — single backtest, next-bar fills, no walk-forward, no selection-bias gates. Real verdicts come from the Python pipeline (walk-forward, deflated Sharpe, permutation test, Monte-Carlo bust probability).

## ORB recipe (the example system)

- Build ORH/ORL/ORM from **high/low** over an Opening Range window (default 09:30–10:00 ET).
- Signal computed on a fixed **Signal timeframe** (independent of chart TF) via `request.security`.
- Entry: **N consecutive signal-TF closes** beyond ORH (long) / ORL (short); a close back inside resets the counter.
- Risk: **R = opening-range width**, anchored to the rails. Stop = 1R (opposite rail), target = R-multiple.
- Flat by end of regular session. One trade per session (optional).
