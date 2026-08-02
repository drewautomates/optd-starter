"""Test 1 · FIT — the cheat ladder, on pure random data.

Run:  python backtests/runs/run_cheat_demo.py

Let the backtest cheat, then take the cheats away one at a time and watch what
survives. Random-walk sessions have NO real edge, so the honest number must be
~0 (worse, after costs). Everything above it was manufactured.

Four passes. Same signals, same stops, same targets, every run — the ONLY thing
that changes is the price you actually get filled at:

  P0  fantasy       enter at the signal bar's CLOSE, no commission, touch = fill
  P1  honest entry  enter at the next bar's OPEN (a price you could reach), + commission
  P2a honest fills  + intrabar sequencing: a level only fills if the tape got there first
  P2b + slippage    + 0.53 ticks/side crossing cost, measured off ES, not assumed

  P0 -> P1   = the entry you couldn't have had
  P1 -> P2a  = the fill model itself
  P2a -> P2b = plain slippage

That split is the point. "It died of slippage" is a boring result everyone
already discounts. "It died of fills that never happened" is the actual claim,
and you can only support it by separating the two.

If a strategy still loses at P0, you are done — nothing else needs checking.

To run it for real: point `load_bars_csv` at your own 1-minute data instead of
`synth_session`. Same code, real fills.
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "backtests"))
sys.path.insert(0, os.path.join(ROOT, "indicators", "python"))

from costs import CHEAT, COMMISSION_ONLY, FULL, Costs  # noqa: E402
from data import synth_session            # noqa: E402
from kernels import honest_exit, validate_kernels  # noqa: E402
from orb import orb_signals               # noqa: E402

N_SESSIONS = 800

# Contract specifics and rates live in costs.py, so the ladder here reads as what
# it is: the same trade, priced four ways. Swap the presets for your own broker's
# schedule in one place and every pass moves together.
PASSES = [
    # label,             honest_entry, mode,     costs
    ("P0  fantasy",      False,        "naive",  CHEAT),
    ("P1  honest entry", True,         "naive",  COMMISSION_ONLY),
    ("P2a honest fills", True,         "honest", COMMISSION_ONLY),
    ("P2b + slippage",   True,         "honest", FULL),
]


def _run_pass(bars, tr, honest_entry: bool, mode: str, costs: Costs) -> float | None:
    """One trade under one fill model. Returns net dollars, or None if unfillable."""
    i = tr["entry_idx"]
    slip = costs.slip_points()

    if honest_entry:
        # You cannot trade the close of the bar that produced the signal — that
        # price is only known once the bar is over. The next open is the first
        # price you could actually have reached.
        if i + 1 >= len(bars):
            return None
        entry = bars[i + 1].open
    else:
        entry = tr["entry"]

    if slip:
        # You cross the spread to get in: pay up long, down short.
        entry += slip if tr["side"] == "long" else -slip

    # Stops and targets never move — only the fill price does. That is the
    # whole experiment: one variable.
    if abs(entry - tr["stop"]) == 0:
        return None
    reason, exit_price, _r = honest_exit(tr["side"], i, entry, tr["stop"],
                                         tr["target"], bars, mode)

    if slip and reason == "stop":
        # A stop is a market order — you cross to get out too. A target is a
        # resting limit: it doesn't slip, it just might never fill, which is
        # what the honest fill model already accounts for.
        exit_price -= slip if tr["side"] == "long" else -slip

    points = (exit_price - entry) if tr["side"] == "long" else (entry - exit_price)
    return points * costs.point_value - costs.commission_round_turn()


def main() -> None:
    # The kernel proves itself honest before we trust a single number.
    validate_kernels()
    print()

    results: dict[str, list[float]] = {label: [] for label, *_ in PASSES}

    for seed in range(N_SESSIONS):
        bars = synth_session(seed)
        # Tight 1:1 bracket: on random data the TRUE expectancy is provably 0,
        # so any positive number is unambiguously the cheats, not the strategy.
        for tr in orb_signals(bars, r_mult=1.0, fixed_r=1.0):
            for label, honest_entry, mode, costs in PASSES:
                net = _run_pass(bars, tr, honest_entry, mode, costs)
                if net is not None:
                    results[label].append(net)

    n = len(results["P0  fantasy"])
    print(f"ORB on {N_SESSIONS} random-walk sessions  ({n} trades, 1 contract ES)\n")
    print(f"{'pass':<20}{'net $':>12}{'$/trade':>12}{'win rate':>12}{'delta':>12}")
    print("-" * 68)

    prev = None
    for label, *_ in PASSES:
        rs = results[label]
        if not rs:
            continue
        total = sum(rs)
        wr = sum(1 for r in rs if r > 0) / len(rs)
        delta = "" if prev is None else f"{total - prev:>+12,.0f}"
        print(f"{label:<20}{total:>12,.0f}{total / len(rs):>12.2f}{wr:>11.1%}{delta:>12}")
        prev = total

    print("-" * 68)
    fantasy, honest = sum(results["P0  fantasy"]), sum(results["P2b + slippage"])
    print(f"\nthe data was random. there was never an edge to find.")
    print(f"the fantasy pass reported ${fantasy:,.0f}. the honest one reports "
          f"${honest:,.0f}.")
    print(f"that ${fantasy - honest:,.0f} gap is not a strategy result. it is the "
          f"cheats, priced.")
    print("\nif yours still loses at P0, stop there. nothing else needs checking.")


if __name__ == "__main__":
    main()
