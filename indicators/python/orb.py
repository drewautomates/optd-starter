"""ORB signal in Python — parity with the Pine reference (the spec).

Mirrors indicators/pine_reference/Opening_Range.pine:
  - Opening range = high/low of the first `or_minutes` of the session.
  - Entry on `n_confirm` consecutive closes beyond a rail (long above ORH, short below ORL).
  - R = stop distance; stop = the opposite rail; target = entry +/- r_mult * R.
  - One trade per session (the first rail to trigger).

This is the parity layer the README promised. Pine stays the source of truth; when
they disagree, fix both in the same change.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "backtests"))

from data import Bar  # noqa: E402


def orb_signals(bars: list[Bar], or_minutes: int = 30, n_confirm: int = 1,
                r_mult: float = 1.5, fixed_r: float | None = None) -> list[dict]:
    """Return the session's ORB trade as a list of 0 or 1 dict(s).

    By default the stop is the **opposite rail** (Pine-parity; R = OR width).
    Pass `fixed_r` for the common tight-stop intraday variant (stop = a fixed
    distance from entry) — that's the regime where the same-bar fills lie bites,
    because the stop and target are close enough to share a single bar.
    """
    if len(bars) <= or_minutes:
        return []
    orh = max(b.high for b in bars[:or_minutes])
    orl = min(b.low for b in bars[:or_minutes])

    run_long = run_short = 0
    for i in range(or_minutes, len(bars)):
        c = bars[i].close
        run_long = run_long + 1 if c > orh else 0
        run_short = run_short + 1 if c < orl else 0
        if run_long >= n_confirm:
            stop = (c - fixed_r) if fixed_r else orl
            return [_trade(i, "long", c, stop, c + r_mult * (c - stop))]
        if run_short >= n_confirm:
            stop = (c + fixed_r) if fixed_r else orh
            return [_trade(i, "short", c, stop, c - r_mult * (stop - c))]
    return []


def _trade(idx: int, side: str, entry: float, stop: float, target: float) -> dict:
    return {"entry_idx": idx, "side": side, "entry": entry, "stop": stop,
            "target": target, "R": abs(entry - stop)}
