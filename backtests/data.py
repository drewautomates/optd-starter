"""Data layer — bars + the intrabar truth.

The honest-fills story turns on one fact a daily/1-min OHLC backtest throws away:
*within a bar, did the high print before the low, or after?* That ordering decides
which of your two exits (stop vs target) actually filled first when both are inside
the same bar. Tick data knows it. OHLC doesn't — so most backtests guess, optimistically.

This module gives you:
  - `Bar`            — one bar, carrying `up_first` (the intrabar truth).
  - `synth_session`  — a deterministic synthetic session for the public demo.
  - `load_bars_csv`  — load your own 1-min CSV (you supply `up_first`, or it's
                       conservatively unknown).

THE PRODUCTION HOOK: the rest of the pipeline only ever calls `load_bars()`-shaped
data (a list of `Bar`). On the real desk, a private adapter reads native Sierra
Chart .scid tick files and fills `up_first` from the actual tick sequence — same
interface, real ticks. That adapter (and the real data) stays private; everything
here runs on synthetic or your-own data so the demo is fully reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Bar:
    """One bar. `up_first` is the intrabar truth: did the HIGH print before the LOW?

    With OHLC alone you don't know this — that's the whole problem. Synthetic data
    sets it from a simulated intrabar path; real tick data sets it from the ticks.
    `None` means genuinely unknown (an honest backtest then assumes the *adverse*
    order — never the convenient one).
    """

    t: int          # minute index within the session
    open: float
    high: float
    low: float
    close: float
    up_first: bool | None = None


def synth_session(seed: int, n_minutes: int = 390, start: float = 5000.0,
                  step_vol: float = 1.25, intrabar_steps: int = 6) -> list[Bar]:
    """A deterministic synthetic trading session — a pure random walk.

    Pure random walk is the point: a random series has **no real edge**, so any
    positive expectancy a backtest reports on it is an artifact. The honest fills
    will show ~0; the naive fills will manufacture a fake edge from thin air. That
    gap is the lie, isolated.

    Each minute is built from a mini intrabar walk, so `high`, `low`, and crucially
    `up_first` are all derived from a real (simulated) path — not assumed.
    """
    rng = np.random.default_rng(seed)
    bars: list[Bar] = []
    price = start
    for t in range(n_minutes):
        o = price
        path = [o]
        for _ in range(intrabar_steps):
            path.append(path[-1] + rng.normal(0.0, step_vol))
        hi, lo = max(path), min(path)
        # the intrabar truth: index of the high vs the low along the path
        up_first = path.index(hi) < path.index(lo)
        bars.append(Bar(t=t, open=o, high=hi, low=lo, close=path[-1], up_first=up_first))
        price = path[-1]
    return bars


def load_bars_csv(path: str, up_first_col: str | None = "up_first") -> list[Bar]:
    """Load a 1-minute OHLC CSV into `Bar`s.

    Columns: t,open,high,low,close[,up_first]. If you don't have `up_first` (you
    only have OHLC), leave it out — the honest kernel will treat the order as
    unknown and resolve conservatively. That's the honest cost of OHLC-only data,
    and it's exactly why real tick data (the production adapter) is worth it.
    """
    import csv

    bars: list[Bar] = []
    with open(path, newline="") as f:
        for i, row in enumerate(csv.DictReader(f)):
            uf = None
            if up_first_col and row.get(up_first_col, "") != "":
                uf = str(row[up_first_col]).strip().lower() in ("1", "true", "t", "yes")
            bars.append(Bar(t=int(row.get("t", i)), open=float(row["open"]),
                            high=float(row["high"]), low=float(row["low"]),
                            close=float(row["close"]), up_first=uf))
    return bars
