# CLAUDE.md — OPTD Starter

Context for Claude Code working in this repo.

## What this is

A starter template for building and backtesting trading systems with Claude Code + TradingView + Sierra Chart. The flagship example is an **Opening Range Breakout (ORB)** in Pine Script (indicator + strategy). The Python layer is live: a parity ORB (`indicators/python/orb.py`), the honest-fills kernel (`backtests/`), the three bias tests (`backtests/runs/`), and a teaching Sierra Chart `.scid` tick reader (`backtests/ticks.py`). The same ORB also exists as a Sierra Chart **ACSIL signal study** in C++ (`sierra/studies/OPTD_Opening_Range.cpp`) — see `sierra/DEPLOY.md`. Deeper validation gates (walk-forward, permutation, Monte-Carlo) are not built yet — treat them as absent, not as code to go find.

> **Forked this?** This file is yours to edit. Replace the author tag below with your own, and delete anything that describes the upstream project rather than your work.

Author/brand of the upstream template: **OPTD** (`onepersontradedesk.com`). Tone: engineering + honesty + earned intuition. "Honest ___" is the house qualifier.

## Environment

- **Python 3.9+**, and the only dependency is **numpy** (`python3 -m pip install -r requirements.txt`).
- **The interpreter is `python3` on macOS/Linux and `python` (or `py -3`) on Windows.** Don't assume `python` exists — modern macOS and most Linux distros don't ship it. When writing docs or scripts, prefer `python3 -m pip` over bare `pip` for the same reason.
- Scripts resolve their own paths from `__file__`, so they run from **any** working directory and need no `PYTHONPATH` or virtualenv layout.
- **No market data is required.** Every demo generates deterministic synthetic sessions, so results are reproducible offline and identical on any machine.

## Commands

```bash
python3 backtests/runs/run_gauntlet.py     # all three bias tests, end to end
python3 backtests/runs/run_cheat_demo.py   # 1 - FIT   the cheat ladder
python3 backtests/runs/run_fills_demo.py   # 2 - FILL  naive vs honest fills
python3 backtests/runs/run_drift_demo.py   # 3 - FLUKE signal vs drift control
python3 backtests/runs/run_scid_demo.py    # .scid ticks -> bars -> honest fills
```

## Where things go

| Path | Purpose |
|------|---------|
| `indicators/pine_reference/` | Pine Script — the **spec**. The source of truth for any logic. |
| `indicators/python/` | Python reimplementations that must stay in **parity** with the Pine. |
| `backtests/data.py` | `Bar` (with `up_first`, the intrabar truth) + synthetic sessions (`drift_per_min`) + CSV loader. |
| `backtests/costs.py` | `Costs` (commission, slippage, contract specs) + the cheat-ladder presets `CHEAT` / `COMMISSION_ONLY` / `FULL`. Test 1. |
| `backtests/fills.py` | Fill models — naive (the lie) vs honest. Test 2. |
| `backtests/drift.py` | The no-signal control (`drift_trade`) + paired scoring against the noise floor (`compare_to_drift`). Test 3. |
| `backtests/kernels.py` | Validated exit kernels (entry → stop/target → exit price/R) + `validate_kernels()` self-test. `honest_exit_detail` also returns the exit bar index, which the drift control needs. |
| `backtests/ticks.py` | Teaching `.scid` reader — parse ticks, rebuild bars, derive `up_first`. |
| `backtests/runs/` | Runnable demos (`run_*.py`, tracked); saved outputs (gitignored). `run_gauntlet.py` runs the three bias tests (FIT / FILL / FLUKE) end to end. |
| `research/prompts/` | One-shot prompt library — paste into Claude Code to (re)generate artifacts. |
| `research/notebooks/` | Exploratory analysis. |
| `data/tick/`, `data/cache/` | Raw + cached market data. **Gitignored.** See `data/README.md`. |
| `sierra/studies/` | Sierra Chart ACSIL (C++) studies. **Source of truth** — never edit the deployed copy in `ACS_Source`. |
| `sierra/scripts/` | `deploy.ps1` / `deploy.sh` — copy `sierra/studies/*` into a Sierra Chart `ACS_Source`. |
| `sierra/DEPLOY.md` | Deploy → build → load → verify, and the four failure modes. |
| `journal/schema.sql` | Trade journal DB schema. |

## Conventions

- **Pine is the spec.** When Pine and Python disagree, Pine wins (or you fix both in the same change). Note parity in commits.
- **Pine Script v6.** Author tag `OPTD` — change it to your own handle if you forked this.
- **Sierra Chart / ACSIL.** One study per file, `SCDLLName("OPTD_Studies")`, study functions prefixed `scsf_OPTD_`. Every threshold, time and count is a user input — no constants buried in logic. ASCII only in any string that reaches the Sierra Chart message log. **Signal studies are signals only**: they draw levels and mark bars, and never place, modify or manage an order or touch the trading API. Claude Code cannot compile ACSIL — the build is a GUI action inside Sierra Chart, so deploy and then ask for the build output. **ACSIL has a small public corpus, which is exactly the condition under which a model invents a plausible function that does not exist**: if you are not certain a signature exists, find it in the `ACS_Source` examples that ship with Sierra Chart and say which file and function you took it from, or stop. Do not guess a signature.
- **Standalone and portable.** This repo is public and gets cloned onto machines nothing like the one it was written on. So:
  - **No absolute paths, ever.** Resolve from `__file__` or the repo root, never from a home directory or a drive letter.
  - **No machine-specific config** — no hardcoded data directories, broker accounts, platform install paths, or environment variables the reader doesn't have.
  - **No required market data.** Demos generate their own synthetic sessions; anything reading real data must degrade to a clear message, not a traceback.
  - **All printed output stays ASCII.** A Windows console on a legacy code page dies on an em dash with `UnicodeEncodeError`. Typography is fine in comments, docstrings, and Markdown — never in a `print()`.
  - **Every `open()` on a text file passes `encoding=`.** Bare `open()` uses the locale encoding: UTF-8 on macOS/Linux, cp1252 on Windows. Use `utf-8-sig` when reading anything a user might have exported from Excel, so the BOM doesn't corrupt the first column name.
  - **Binary formats are explicitly little-endian and explicitly sized** — `struct.Struct("<q4f4I")`, never native `@`/`=` formats, whose sizes and alignment vary by platform.
  - **Build paths with `os.path.join`/`pathlib`**, never string concatenation with `/` or `\`.
  - **Nothing private.** No real account data, no proprietary strategy internals, no paths into a private repo. Assume every file here is read by strangers.
- **Honest backtesting.** The TradingView Strategy Tester is a first sniff, not proof — single backtest, next-bar fills, no walk-forward, no selection-bias gates. Real verdicts come from the Python pipeline (walk-forward, deflated Sharpe, permutation test, Monte-Carlo bust probability).

## ORB recipe (the example system)

- Build ORH/ORL/ORM from **high/low** over an Opening Range window (default 09:30–10:00 ET).
- Signal computed on a fixed **Signal timeframe** (independent of chart TF) via `request.security`.
- Entry: **N consecutive signal-TF closes** beyond ORH (long) / ORL (short); a close back inside resets the counter.
- Risk: **R = opening-range width**, anchored to the rails. Stop = 1R (opposite rail), target = R-multiple.
- Flat by end of regular session. One trade per session (optional).
