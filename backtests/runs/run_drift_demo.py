"""Test 3 · FLUKE — the drift control, in a flat market and a rising one.

Run:  python backtests/runs/run_drift_demo.py

Take the signal away and keep everything else. Same entry times, same exit
times, same exposure — just be long, ignoring what the strategy thought it saw.

That separates the two things a strategy can be paid for:

  showing up        being in the market during those hours
  knowing something the signal itself

If the signal knows something, it has to beat the version that doesn't. If it
doesn't beat it, you don't have a strategy — you have market drift wearing a
costume, and the backtest will never tell you, because the backtest only ever
ran the version WITH the signal.

Two regimes, because this test only bites in one of them:

  FLAT    a driftless random walk. Nothing to ride. Control earns ~0.
  RISING  the same walk with an upward drift. Now the control earns real money
          per trade — and the strategy has to clear it to be worth anything.

The second case is the honest one, and it's the one that matches a decade of
backtests run on an index that mostly went up.

All fills are honest and commissioned throughout — this test is about the
signal, so nothing else is allowed to vary.

Every gap is reported against its own noise floor. The two legs trade the same
bars, so they're scored as a PAIRED difference: most of the variance is the
market's and cancels, leaving the part the signal is responsible for. A gap
smaller than that floor is reported INCONCLUSIVE, not as a win — that rule
disqualifies more strategies than the three tests do.
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "backtests"))
sys.path.insert(0, os.path.join(ROOT, "indicators", "python"))

from costs import COMMISSION_ONLY         # noqa: E402
from data import synth_session            # noqa: E402
from drift import compare_to_drift, drift_trade  # noqa: E402
from kernels import honest_exit_detail, validate_kernels  # noqa: E402
from orb import orb_signals               # noqa: E402

N_SESSIONS = 800

# Honest fills, commission on both legs, no slippage: this test is about the
# signal, so nothing else is allowed to vary between the two legs.
COSTS = COMMISSION_ONLY

# Per-minute drift. Small on purpose: ~0.36 pts/min is an ordinary up year, not
# a melt-up. The test should work on a realistic tape.
RISING_DRIFT_PER_MIN = 0.36


def _net(side: str, entry: float, exit_price: float) -> float:
    points = (exit_price - entry) if side == "long" else (entry - exit_price)
    return points * COSTS.point_value - COSTS.commission_round_turn()


def _regime(drift_per_min: float) -> dict:
    trades: list[dict] = []

    for seed in range(N_SESSIONS):
        bars = synth_session(seed, drift_per_min=drift_per_min)
        for tr in orb_signals(bars, r_mult=1.0, fixed_r=1.0):
            i = tr["entry_idx"]
            if i + 1 >= len(bars):
                continue
            entry = bars[i + 1].open          # honest entry, both legs
            if abs(entry - tr["stop"]) == 0:
                continue

            # The kernel hands back WHEN the trade ended as well as at what
            # price, so the control can exit on the same bar without a second
            # walk that could drift out of agreement with it.
            _reason, exit_price, _r, exit_idx = honest_exit_detail(
                tr["side"], i, entry, tr["stop"], tr["target"], bars, "honest")

            trades.append({
                "side": tr["side"],
                "net": _net(tr["side"], entry, exit_price),
                # The control: in at the same bar and the same price, out at the
                # same bar, always long, signal discarded entirely.
                "drift_net": drift_trade(bars, i + 1, exit_idx, "long", COSTS,
                                         entry_price=entry),
            })

    n = len(trades)
    longs = sum(1 for t in trades if t["side"] == "long")
    return {**compare_to_drift(trades), "long_pct": (longs / n if n else 0.0)}


def main() -> None:
    validate_kernels()
    print()

    for name, drift_per_min in (("FLAT  (driftless walk)", 0.0),
                                ("RISING (walk + drift)", RISING_DRIFT_PER_MIN)):
        r = _regime(drift_per_min)
        n = r["n"]
        print(f"{name}   {n} trades, {r['long_pct']:.0%} long")
        print("-" * 60)
        print(f"{'':<22}{'net $':>14}{'$/trade':>14}")
        print(f"{'strategy (signal)':<22}{r['strategy_per_trade'] * n:>14,.0f}"
              f"{r['strategy_per_trade']:>14.2f}")
        print(f"{'control (no signal)':<22}{r['drift_per_trade'] * n:>14,.0f}"
              f"{r['drift_per_trade']:>14.2f}")
        print(f"{'edge over drift':<22}{r['edge_per_trade'] * n:>+14,.0f}"
              f"{r['edge_per_trade']:>+14.2f}")
        # The gap alone is not the result. Paired against its own noise floor is.
        print(f"{'noise floor (+/-1 se)':<22}{'':>14}{r['edge_se']:>14.2f}"
              f"   t={r['edge_t']:+.2f}")
        print(f"\n  -> {r['verdict']}\n")

    print("=" * 60)
    print("a strategy that only beats zero has not been tested against")
    print("anything. test it against the version of itself that doesn't")
    print("know anything, and see which one you'd rather own.")
    print("\nten minutes to run on whatever you're already trading.")


if __name__ == "__main__":
    main()
