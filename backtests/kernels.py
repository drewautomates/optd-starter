"""Validated exit kernels — entry -> stop/target -> exit price + realized R.

`honest_exit` walks the bars after entry and returns the first real exit, priced
honestly. `validate_kernels` is the self-test that runs before any sweep: it builds
a bar where the stop was truly hit first and asserts the kernel **refuses to book
the convenient win**. If a bias can be caught by code, catch it in code.

>>> This is the TEACHING kernel — the method, runnable, on synthetic data. <<<
The PRODUCTION kernel on the live desk carries more gates (gap-through fills, partial
fills, queue position, slippage, session edges), reads real Sierra Chart .scid tick
data, and feeds the full validation gauntlet — that runs privately and ships in the
OPTD community (onepersontradedesk.com). The honesty rule is identical either way:
never realize a price the market didn't reach.

Run the self-test directly:  python backtests/kernels.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data import Bar                       # noqa: E402
from fills import resolve_long, resolve_short  # noqa: E402


def honest_exit(side: str, entry_idx: int, entry_price: float, stop: float,
                target: float, bars: list[Bar], mode: str = "honest") -> tuple[str, float, float]:
    """Resolve a trade. Returns (reason, exit_price, realized_R).

    reason is "target" | "stop" | "eod". `mode` is "honest" or "naive" (the lie).
    R is the stop distance, so a stop is always -1.0R.
    """
    R = abs(entry_price - stop)
    if R == 0:
        raise ValueError("zero risk: entry price equals stop")
    resolve = resolve_long if side == "long" else resolve_short
    for bar in bars[entry_idx + 1:]:
        hit = resolve(bar, stop, target, mode)
        if hit is not None:
            reason, price = hit
            return reason, price, _realized_r(side, entry_price, price, R)
    # never hit a level — flat at the last close (end of data / session)
    price = bars[-1].close
    return "eod", price, _realized_r(side, entry_price, price, R)


def _realized_r(side: str, entry: float, exit_price: float, R: float) -> float:
    signed = (exit_price - entry) if side == "long" else (entry - exit_price)
    return signed / R


def validate_kernels() -> None:
    """Fail loudly if the kernel ever books a fill the market didn't earn."""

    # Case 1 — the lie, isolated. Long with stop=99, target=101.5 (R=1.0).
    # The next bar straddles BOTH levels, and the intrabar truth says the LOW
    # printed first (up_first=False) -> the stop was hit first. Honest must book
    # the -1R loss; naive books the convenient +1.5R win.
    straddle = Bar(t=1, open=100, high=102, low=98, close=100, up_first=False)
    bars = [Bar(t=0, open=100, high=100, low=100, close=100), straddle]
    reason_h, price_h, r_h = honest_exit("long", 0, 100.0, 99.0, 101.5, bars, "honest")
    reason_n, price_n, r_n = honest_exit("long", 0, 100.0, 99.0, 101.5, bars, "naive")
    assert reason_h == "stop" and r_h == -1.0, f"honest must book the stop, got {reason_h} {r_h}"
    assert reason_n == "target" and r_n == 1.5, f"naive books the phantom win, got {reason_n} {r_n}"
    assert r_n != r_h, "the whole point: naive and honest disagree on this bar"

    # Case 2 — only the target is in range: both modes agree it's a win.
    clean = Bar(t=1, open=100, high=102, low=99.6, close=101.6, up_first=True)
    bars = [Bar(t=0, open=100, high=100, low=100, close=100), clean]
    for m in ("honest", "naive"):
        reason, _, r = honest_exit("long", 0, 100.0, 99.0, 101.5, bars, m)
        assert reason == "target" and r == 1.5, f"{m}: clean target should win, got {reason} {r}"

    # Case 3 — no level touched: flat at the last close (EOD), priced honestly.
    inside = [Bar(t=0, open=100, high=100, low=100, close=100),
              Bar(t=1, open=100, high=100.4, low=99.6, close=100.2, up_first=True)]
    reason, price, r = honest_exit("long", 0, 100.0, 99.0, 101.5, inside, "honest")
    assert reason == "eod" and price == 100.2 and abs(r - 0.2) < 1e-9, f"EOD flat failed: {reason} {price} {r}"

    print("validate_kernels: PASS — the kernel refuses to book a price the market never reached.")


if __name__ == "__main__":
    validate_kernels()
