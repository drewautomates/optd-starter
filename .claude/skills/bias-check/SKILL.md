---
name: bias-check
description: Audit a trading backtest for lookahead and other biases. Point it at a directory of backtest code; it maps the pipeline from raw data to the equity number, reviews every indicator for lookahead and repainting, runs probes against the real code, and reports where the number may be fake, with the file and line and the test that proves it. Uses this repo's honest kernels, fills and drift control as the reference. Triggers on "bias check", "check my backtest", "is my backtest lying", "audit this strategy for lookahead", "review my indicators", "review my pipeline".
---

# bias-check

A backtest is a claim: *if I had traded this, this is what would have happened.* This skill
treats it like a witness. Most of the time it isn't lying on purpose. It remembers things it
couldn't have known, fills at prices nobody got, and forgets the bill.

**The output is a list of places where the number may be fake, each with evidence.** It is not
a verdict that a strategy works. A clean report means these checks found nothing, and nothing more.

## How to call it

```
/bias-check <path-to-your-backtest-folder>
```

Launch Claude Code **inside this repo** (`optd-starter`) — that's what registers the skill — and pass
the path to your backtest. The target can be anywhere on disk; this repo is the reference
implementation, not the thing being checked. With no path, ask for one.

Harnesses live in the target folder but import from this repo, so start each one with:

```python
import sys; sys.path.insert(0, r"<absolute path to optd-starter>/backtests")
from probes import prefix_invariance, warmup_sensitivity
```

## Ground rules

1. **Read-only on the user's code.** Never edit their files. Every probe, harness or re-run goes in
   `<target>/_bias_check/`, which you create. Say so at the start. Run Python with `python -B` (or
   `PYTHONDONTWRITEBYTECODE=1`) so no `__pycache__` lands in their folder, and run their scripts from
   the directory they expect — relative data paths depend on it.
2. **Run it, don't guess.** A finding backed only by reading code is 🟡 at most. A finding is 🔴 when
   a probe or a side-by-side re-run shows the number move.
3. **Reproduce before you change anything.** Most retail backtests are one top-level script, not
   functions. Port the loop into a function in `_bias_check/`, keep it line-for-line, and assert it
   reproduces the headline number exactly (trade count and net) before any re-run. Every re-run after
   that is on the port; say so in the report.
4. **One variable per re-run, then the ladder.** Change one thing (the bar index, the entry bar, the
   timezone, the fill model) and report it against the original, side by side. Then stack every fix
   in order and report the fully honest number — that's the one the user actually wants.
5. **Measure the direction of a bias, don't assume it.** Some fixes make results *worse than
   reality*. If a re-run moves the number the "wrong" way, report that too.
6. **Nothing leaves the machine.** Don't upload their data or code anywhere.
7. If you can't run their code (missing data, missing dependencies), say exactly what's missing,
   keep going on the static review, and mark every finding you couldn't run as "not run".

## Step 1 — Map the pipeline

Before judging anything, write down how the number is made. Find each stage and cite `file:line`:

| Stage | What to find |
|---|---|
| Data | Where bars/ticks load from. Resolution. Timezone of the index. Session filter. |
| Bars | Are higher-timeframe bars built from lower ones, loaded separately, or requested from a platform? Is a bar's timestamp its **open** or its **close**? |
| Indicators | Every indicator and every feature the signal reads, and the timeframe of each. |
| Signal | The exact condition, and the bar it's evaluated on. |
| Entry | The price and bar the trade enters at. |
| Exits | Stop, target, trail, time exit. How a bar that touches both stop and target is resolved. |
| Costs | Commission, slippage, per contract or per point. |
| Accounting | How P&L is summed. Equity frequency for drawdown. Denominator for "per month". |
| Selection | How many variants/parameters were tried before this one was picked. |

Put the map at the top of the report and keep going; don't stop to wait for approval. Mistakes live
between stages, so an unmapped stage is an unchecked stage.

Two rows can't be answered from code — **ask the user up front, once**: how many variants were tried
before this one (Selection), and whether they have a chart export of the same indicator from the
platform they trade (Step 3 parity). Carry on without the answers; list them under "Not run".

## Step 2 — Lookahead (the most expensive bias, check it first)

Lookahead looks like the best edge you've ever found. The same bar-timing mistake comes back in
new forms, so ask these of **every** signal and indicator, not just the first:

1. **Signal bar vs next bar.** Does the backtest enter at the close (or inside) of the bar that
   produced the signal? That price is only known once the bar is over. Re-run with entry at the next
   bar's open and show both.
2. **Higher timeframe, forming vs completed.** When a 1-minute signal reads a 10-minute (or hourly,
   daily) input, which bar does it read at minute 1 and at minute 9 of the period? Built from
   finished data, the current higher-timeframe bar is already complete, so its close is in the
   future. Look for `resample` + `ffill`/`reindex` without a shift, `searchsorted(..., side="right")`,
   `merge_asof` on bar-open timestamps, `request.security` with `lookahead_on`, and platform
   "higher timeframe" reads indexed on the current bar.
3. **Bar timestamp = start or end?** A bar stamped at its open but priced at its close lets the
   simulation start before the entry price existed.
4. **When does the price path start?** If exits are simulated from ticks or lower bars, does the path
   begin at the entry time, or at the start of the signal bar?
5. **Same-day or same-bar labels.** Any feature constant for the whole session (a daily value, a
   "day type" label) — when was it actually known? If it uses today's close, it's future data in
   every morning bar.
6. **Lags.** Trace each outside input from its raw file to the column the strategy reads. Is each step
   "as of the close of day D" or "in effect during day D"? Two correct components can each add a lag.
7. **Timezones.** What timezone is the index in? Print the first and last bar the session filter keeps
   on one sample day, and how many bars it keeps against the instrument's regular session (for US
   index futures: 6:30–13:00 Pacific = 390 one-minute bars; confirm the instrument and watch the DST
   switch dates). A UTC index read as local time keeps the wrong hours and can produce a believable
   fake edge. Also check weekends and holidays are excluded.
8. **Repainting.** Does any indicator's past value change as new bars arrive, or depend on how much
   history was loaded?

### The probes (run these)

`backtests/probes.py` in this repo has two, and they don't need to understand the code:

- **`prefix_invariance(indicator, bars)`** — compute on the full data, then again with every bar after
  `i` deleted. If the value at `i` changes, it read the future. This is the one that catches a
  forming higher-timeframe bar.
- **`warmup_sensitivity(indicator, bars)`** — compute from different history start dates and diff the
  recent bars. If they disagree after warm-up, the backtest depends on how much history was loaded.
  Keep at least one offset that is **not** a multiple of the higher-timeframe period (the defaults are
  0, 7, 53). Higher-timeframe bars built by counting rows (`i // 10`) instead of reading the clock
  pass any offset that's a multiple of 10 and fail the others.

**Size them.** `prefix_invariance` re-runs the indicator once per checkpoint. On a year of 1-minute
data that's hours. Slice to one or two sessions and pass that session's indices as `checkpoints` —
a timing bug is systematic, so one session catches it.

**Timestamps.** `data.load_bars_csv` keeps only a minute index and OHLC. Anything clock- or
timezone-dependent (session filters, clock-aligned higher-timeframe bars) needs the user's own
timestamps: wrap their loader, or pass timestamps alongside the bars in the harness.

Wrap each of the user's indicators and signal functions as `indicator(bars) -> one value per bar`
in a harness under `_bias_check/`, load their data (or `data.load_bars_csv`), and run both probes.
If their code isn't Python, port only the read being tested, keep the port line-for-line, and say
it's a port. `backtests/runs/run_lookahead_demo.py` is the worked example: the same strategy on
random data makes money with the forming 10-minute read and loses with the completed one.

## Step 3 — Indicator review

For each indicator the signal reads:

- Its timeframe, and which bar of that timeframe is read at signal time (from Step 2).
- `prefix_invariance` result. `warmup_sensitivity` result.
- **Parity:** if the same indicator exists on a charting platform and in the backtest, do they agree
  on the same bars? Pick 20 bars and compare. A backtest indicator that doesn't match the chart
  you'll trade from is testing a different strategy.
- **Degenerate values:** print each input's distribution before its effect. Constant, all-zero, or
  all-identical inputs get reported as "no effect" when they're really broken.
- **Invariants:** high ≥ low, worst excursion ≥ realised loss, no values outside the physical range.
- **Preconditions that never fire:** count how often each condition blocks a signal.

## Step 4 — The rest of the pipeline

Compare their code against this repo's reference implementation at each stage:

| Check | Question | Reference here |
|---|---|---|
| Fills | When stop and target both sit inside one bar, which one fills? Bar data can't say which printed first; a backtest that picks the favourable one is guessing in your favour. For every stop exit, was the fill inside the range that actually traded? | `backtests/fills.py`, `backtests/kernels.py` (`validate_kernels`), `run_fills_demo.py`. Note `honest_exit` starts checking at the bar *after* `entry_idx`: for a next-bar-open entry, pass the signal bar as `entry_idx` or the entry bar's own range is skipped |
| Entry | Signal-bar close vs next-bar open. | `run_cheat_demo.py` pass P0 → P1 |
| Costs | Share of gross paid to commission and slippage. What one extra tick per fill does. Commission is per contract, not per point, so micros carry far more fee drag than full-size. | `backtests/costs.py`, `run_cheat_demo.py` P2b |
| Drift | Would being in the market over the same bars, with no signal, have made the same money? | `backtests/drift.py`, `run_drift_demo.py`. ⚠️ Its control exits at the close with market orders; against a strategy whose target is a resting limit, that gap alone can look like edge. Say so when it applies |
| Portfolio | With one position at a time, how many signals are skipped, and what do the survivors average? Standalone results don't add up. | — |
| Accounting | Drawdown computed on daily (or trade-level) equity, not monthly. "Per month" divided by calendar months, not active days. | — |
| Selection | How many variants were tried? The best of N random tries looks good by chance. Was the threshold or parameter chosen using the data it's reported on? Is there a holdout nobody has looked at? Ask for the trial count and report it next to the result; the more versions tried, the higher the bar a winner has to clear. | — |
| Benchmark | Does it beat doing nothing (buy-and-hold on the same instrument) at matched risk, after costs? | `run_drift_demo.py` |

Re-run their backtest (the port, from rule 3) with the honest version of each stage swapped in, one
at a time, then stacked, and tabulate the number before and after.

**Say when a fix couldn't bite.** If a re-run changes nothing, count the event that would have
triggered it — bars where stop and target were both hit, gaps between one bar's close and the next
bar's open, trades that hit neither level — and report the count. "No change, 0 such bars in this
data" is not the same finding as "safe".

## Step 5 — The too-good-to-be-true triggers

Any of these means audit before believing:

- Sharpe above ~3 on an intraday strategy, or 7–8 on a scalp.
- A win rate well above 55% on a 1:1 bracket.
- A feature that's positive every year and many standard deviations from noise. Real edges wobble
  year to year; a leak works every year because it's reading the answer.
- A big dollar figure from a quick harness, or a result described as "dominates".

## Step 6 — Report

Write `<target>/_bias_check/REPORT.md` and summarise it in chat. Most severe first.

```
# Bias check — <folder> — <date>

**Headline:** the reported <number> becomes <number> when <the biggest single fix>; fully honest it's
<number>. (What moved the number — not a verdict on the strategy.)

## Pipeline map
<the Step 1 table, with file:line>

## Findings
### 🔴 <one-line claim>
- Where: file:line
- What: the mechanism, in one sentence
- Evidence: the probe or re-run, with both numbers side by side
- Fix: the smallest change, as a suggestion (not applied)

### 🟡 <...>    (plausible, not yet proven by a run)
### ⚪ <...>    (ran, didn't move — with the count of triggering events, e.g. "0 same-bar stop+target hits")
### 🔵 <...>    (hygiene: missing test, missing assertion, unlogged trial count)

## Not run
<every check that couldn't run, and what it needs>

## Before and after
| Change | Before | After | (one at a time vs the original, then the stacked ladder)
```

Severity: **🔴** a run shows the number moves. **🟡** the code allows it but no run has shown it yet.
**⚪** it ran and didn't move, because this data never produced the triggering event (give the count;
it can bite on other data). **🔵** a missing safeguard that would have caught a bias.

End with the three cheap checks that did the most work here, and tell the user to rerun this skill
after every change to the signal. A bias fixed once comes back in the next indicator.
