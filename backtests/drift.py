"""The drift control — test three, the one nobody runs.

A strategy can survive every cost you throw at it and still not be a strategy. If
the market drifted up over your test window and your rules happened to keep you long
during the drift, your equity curve is the market's, not yours. You are being paid
for *exposure*, and calling it *edge*.

The control separates the two things a strategy can be paid for:

  showing up at the right time   — being in the market during favourable stretches
  actually knowing something     — the signal itself carrying information

So: enter at exactly the same moments the strategy did. Exit on exactly the same
bars. Then throw the signal away and just take the exposure. If the strategy can't
beat the version of itself that ignores its own rules, the rules were decoration.

There is no stop and no target on the control — that's deliberate. Adding them would
reintroduce the fill question this test is not asking about. The control holds the
position and takes what the market gives over the same bars.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from costs import CHEAT, Costs  # noqa: E402
from data import Bar            # noqa: E402


def drift_trade(bars: list[Bar], entry_idx: int, exit_idx: int,
                side: str = "long", costs: Costs = CHEAT,
                entry_price: float | None = None) -> float:
    """Hold `side` from `entry_idx` to `exit_idx`, ignoring any signal. Returns $.

    Pass `entry_price` when you have the price the strategy actually got. The
    control is supposed to differ from the strategy in *one* way — the signal — so
    handing it the same fill keeps the comparison clean. Left as None it prices
    close-to-close, the conservative reading when there is no fill to inherit: it
    claims no skill about where inside the bar you got in.

    Exit is always the close of `exit_idx`: the control has no stop and no target,
    so there is no level to resolve and no fill question to answer. Both legs are
    market orders, which is the case `round_turn_dollars` is written for.
    """
    # Exiting on the entry bar is a real, common outcome for a tight bracket, and
    # it is only degenerate when we're pricing close-to-close — then there is no
    # holding period at all. Given an explicit fill, open-to-close of that one bar
    # is exactly what the control held, and dropping it would silently delete most
    # of the control's trades on a tight bracket.
    if exit_idx < entry_idx or (exit_idx == entry_idx and entry_price is None):
        return 0.0
    entry = bars[entry_idx].close if entry_price is None else entry_price
    exit_price = bars[exit_idx].close
    points = (exit_price - entry) if side == "long" else (entry - exit_price)
    return points * costs.point_value - costs.round_turn_dollars()


def compare_to_drift(strategy_trades: list[dict]) -> dict:
    """Score a set of executed trades against their own no-signal twin.

    Each entry in `strategy_trades` needs: `net` ($ the strategy made on that
    trade), `drift_net` ($ the no-signal hold made over the same bars), and `side`.

    The headline is `edge_per_trade` — what the signal added, per trade, over doing
    nothing but being there. Zero or negative means the signal is decoration.
    """
    n = len(strategy_trades)
    if n == 0:
        return {"n": 0, "strategy_per_trade": 0.0, "drift_per_trade": 0.0,
                "edge_per_trade": 0.0, "edge_se": 0.0, "edge_t": 0.0,
                "long_share": 0.0, "verdict": "no trades"}

    strat = sum(t["net"] for t in strategy_trades) / n
    drift = sum(t["drift_net"] for t in strategy_trades) / n

    # Score the difference PER TRADE, not the difference of two averages. The two
    # legs share the same bars, so most of their variance is the market's and
    # cancels — pairing removes it and leaves the thing you actually care about.
    # Comparing separate averages instead throws that away and buries a real
    # result (or manufactures one) under noise that was never relevant.
    diffs = [t["net"] - t["drift_net"] for t in strategy_trades]
    edge = sum(diffs) / n
    se = _stderr(diffs)
    t_stat = (edge / se) if se > 0 else 0.0

    # Every quadrant below except the last is a way to fool yourself, and the order
    # matters: the most specific diagnosis has to win, or a strategy that is losing
    # money BECAUSE it's short a rising market gets filed under "it loses money"
    # and the actual finding never gets printed.
    #
    # An edge you cannot separate from noise is not an edge yet, so that check comes
    # first: |t| < 2 means a run of coin flips would produce this difference often
    # enough that you have learned nothing. This rule disqualifies more strategies
    # than any of the three tests do.
    if abs(t_stat) < 2.0:
        verdict = (f"INCONCLUSIVE - the gap is {edge:+,.2f}/trade but the noise floor "
                   f"is +/-{se:,.2f} (t={t_stat:.2f}). you cannot tell this apart "
                   f"from chance. more trades, or no claim.")
    elif edge <= 0 and drift > 0:
        tail = (" and the strategy loses money on top of it" if strat <= 0 else "")
        verdict = (f"FAIL - doing NOTHING over the same bars pays {-edge:,.2f}/trade "
                   f"more{tail}. the signal isn't an edge, it's drift you're paying "
                   f"commission for.")
    elif edge <= 0:
        verdict = ("FAIL - doing nothing over the same bars beat it, in a market that "
                   "wasn't going anywhere either. the signal is decoration.")
    elif strat <= 0:
        verdict = (f"LOSING - it beats its own control by {edge:,.2f}/trade and still "
                   f"loses money. there is nothing here to own.")
    elif drift > 0 and edge < drift * 0.25:
        verdict = ("WEAK - it beats the drift, but most of what it makes IS the "
                   "drift. size that accordingly.")
    else:
        verdict = "PASS - the signal beats its own no-signal twin."

    return {"n": n, "strategy_per_trade": strat, "drift_per_trade": drift,
            "edge_per_trade": edge, "edge_se": se, "edge_t": t_stat,
            "verdict": verdict, "long_share": _long_share(strategy_trades)}


def _stderr(xs: list[float]) -> float:
    """Standard error of the mean. No numpy needed, no dependency added."""
    n = len(xs)
    if n < 2:
        return 0.0
    mean = sum(xs) / n
    var = sum((x - mean) ** 2 for x in xs) / (n - 1)
    return (var / n) ** 0.5


def _long_share(trades: list[dict]) -> float:
    """Fraction of net profit coming from the long side.

    A directional strategy that makes 100%+ of its money long, while the short book
    bleeds, is the tell that sends you to the drift control in the first place —
    especially for anything that claims to work in both directions.
    """
    total = sum(t["net"] for t in trades)
    if total == 0:
        return 0.0
    longs = sum(t["net"] for t in trades if t["side"] == "long")
    return longs / total
