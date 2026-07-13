"""Fill models — the lie and the honest version.

Two ways to resolve a bar when your stop and target are both in play:

  naive   — the optimistic guess almost every retail backtest makes. When both the
            stop and the target are inside the same bar, assume the TARGET filled.
            (Check take-profit first; book the win.) Limits always fill at your price.
            This is not a strawman — it's the TradingView/loop default behavior.

  honest  — use the intrabar truth (`up_first`). If both levels are inside the bar,
            whichever was actually touched first is the fill. If the order is
            genuinely unknown, assume the ADVERSE one. Never book a price the
            market didn't reach before the exit.

The gap between these two, aggregated over a backtest, is the phantom edge.
"""

from __future__ import annotations

from data import Bar


def resolve_long(bar: Bar, stop: float, target: float, mode: str) -> tuple[str, float] | None:
    """Resolve one bar for a LONG (stop < entry < target). Returns (reason, price) or None."""
    hit_target = bar.high >= target
    hit_stop = bar.low <= stop
    if not hit_target and not hit_stop:
        return None
    if hit_target and not hit_stop:
        return ("target", target)
    if hit_stop and not hit_target:
        return ("stop", stop)
    # both inside the same bar — this is where the lie lives
    if mode == "naive":
        return ("target", target)               # optimistic: book the win
    # honest: high-before-low => target hit first; unknown => assume adverse (stop)
    if bar.up_first is True:
        return ("target", target)
    return ("stop", stop)


def resolve_short(bar: Bar, stop: float, target: float, mode: str) -> tuple[str, float] | None:
    """Resolve one bar for a SHORT (target < entry < stop). Returns (reason, price) or None."""
    hit_target = bar.low <= target
    hit_stop = bar.high >= stop
    if not hit_target and not hit_stop:
        return None
    if hit_target and not hit_stop:
        return ("target", target)
    if hit_stop and not hit_target:
        return ("stop", stop)
    # both inside the same bar
    if mode == "naive":
        return ("target", target)               # optimistic: book the win
    # honest: for a short, target is the low; low-before-high (NOT up_first) => target first
    if bar.up_first is False:
        return ("target", target)
    return ("stop", stop)
