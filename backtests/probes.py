"""Lookahead probes — run your indicator, and let the data say whether it cheats.

Reading code for lookahead works until it doesn't: the bug is usually one index,
one `shift`, one `side='right'`, three files away from the signal. These probes
don't read the code. They run it twice and compare, so the answer comes from the
numbers, not from anyone's opinion of the code.

  - `prefix_invariance`   An indicator's value at bar i must not change when every
                          bar after i is deleted. If it does, it read the future.
                          This is the test that catches a 1-minute signal reading
                          a still-forming 10-minute bar.
  - `warmup_sensitivity`  The same indicator computed from two different history
                          start dates must agree on the recent bars. If it
                          doesn't, the value depends on how much history was
                          loaded — the backtest export and the live chart will
                          disagree, and the backtest is the one that's flattered.

Both take `indicator(bars) -> list` returning one value per bar (None while it
warms up). Wrap your own function in a one-line lambda to match that shape; it
doesn't need to know these probes exist.

Run the self-test directly:  python backtests/probes.py
"""

from __future__ import annotations

import math
import os
import sys
from typing import Callable, Sequence

# No module-level import of this repo's `data`: the bias check imports this file from
# inside someone else's folder, and if they have their own data.py, a bare
# `from data import ...` would silently load the wrong one. Bars are duck-typed here —
# anything the indicator accepts is fine.
Indicator = Callable[[Sequence], Sequence]


def _same(a, b, tol: float) -> bool:
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b):
        return True
    try:
        return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return a == b


def prefix_invariance(indicator: Indicator, bars: Sequence,
                      checkpoints: Sequence[int] | None = None,
                      tol: float = 1e-9) -> dict:
    """Recompute the indicator on bars[:i+1] and compare its last value to the full run's value at i.

    A clean indicator gives the same answer either way, because at bar i it only
    ever had bars 0..i. A value that changes when the future is deleted was
    reading the future. Returns a report dict; `leaks` lists (i, full, truncated).

    `checkpoints` defaults to every bar. That's O(n^2) calls, so on long data pass
    a sample — every bar of one session is plenty to catch a timing bug, because
    a timing bug is systematic, not rare.
    """
    full = list(indicator(bars))
    if len(full) != len(bars):
        raise ValueError(f"indicator returned {len(full)} values for {len(bars)} bars; "
                         "it must return one value per bar")
    idxs = range(len(bars)) if checkpoints is None else checkpoints
    leaks, checked = [], 0
    for i in idxs:
        truncated = list(indicator(bars[: i + 1]))
        if not truncated:
            continue
        checked += 1
        if not _same(full[i], truncated[-1], tol):
            leaks.append((i, full[i], truncated[-1]))
    return {"checked": checked, "leaks": leaks,
            "leak_rate": (len(leaks) / checked) if checked else 0.0,
            "passed": not leaks}


def warmup_sensitivity(indicator: Indicator, bars: Sequence,
                       start_offsets: Sequence[int] = (0, 7, 53),
                       compare_last: int = 100, tol: float = 1e-9) -> dict:
    """Compute from several history start dates and diff the values on the same recent bars.

    Recursive indicators (EMAs, trailing states, regime lines) legitimately depend
    on their seed for a while; after warm-up they should converge. If they still
    disagree on the last `compare_last` bars, the backtest number depends on how
    much history you happened to load, and live won't match it.

    The default offsets are deliberately NOT multiples of 5, 10, 15, 30 or 60. A
    higher-timeframe bar built by counting rows (`i // 10`) instead of reading the
    clock passes any offset that's a multiple of its period, and fails this one.
    """
    n = len(bars)
    if compare_last >= n - max(start_offsets):
        raise ValueError("not enough bars: need len(bars) > max(start_offsets) + compare_last")
    runs = {}
    for off in start_offsets:
        vals = list(indicator(bars[off:]))
        runs[off] = vals[-compare_last:]
    base = runs[start_offsets[0]]
    diffs = {}
    for off in start_offsets[1:]:
        bad = [k for k, (a, b) in enumerate(zip(base, runs[off])) if not _same(a, b, tol)]
        diffs[off] = len(bad)
    return {"compared_bars": compare_last, "mismatches_by_offset": diffs,
            "passed": all(v == 0 for v in diffs.values())}


def _selftest() -> None:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from data import synth_session

    bars = synth_session(seed=7, n_minutes=120)

    def sma3(bs):
        out = []
        for i in range(len(bs)):
            out.append(None if i < 2 else sum(b.close for b in bs[i - 2:i + 1]) / 3)
        return out

    def peeks_next(bs):
        # the bug, isolated: reads bar i+1
        return [bs[i + 1].close if i + 1 < len(bs) else bs[i].close for i in range(len(bs))]

    ok = prefix_invariance(sma3, bars)
    bad = prefix_invariance(peeks_next, bars)
    assert ok["passed"], f"a clean SMA must pass, got {ok['leaks'][:3]}"
    assert not bad["passed"] and bad["leak_rate"] > 0.9, "a next-bar read must be caught"

    wu = warmup_sensitivity(sma3, bars, start_offsets=(0, 10), compare_last=50)
    assert wu["passed"], "a finite-window SMA has no warm-up dependence after 3 bars"

    print("probes: PASS -- the clean indicator passes, the one that reads bar i+1 is caught.")


if __name__ == "__main__":
    _selftest()
