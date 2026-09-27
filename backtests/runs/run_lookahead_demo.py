"""Test 4 · TIME — the higher-timeframe candle that knows its own close.

Run:  python backtests/runs/run_lookahead_demo.py

The most common way a multi-timeframe strategy lies. A 1-minute strategy takes a
trade only when the 10-minute candle agrees with it: long if the 10-minute candle
is green, short if it's red. Reasonable filter. The question is WHICH 10-minute
candle it reads.

  naive   the 10-minute candle the current minute belongs to. At minute 3 of that
          candle, its close is 7 minutes in the future. Built from finished data,
          that bar is already complete, so the backtest reads a close nobody
          watching the chart had yet.
  honest  the last COMPLETED 10-minute candle. That's the only one a live chart
          could have shown you.

Everything else is identical: same breakout rule, same next-bar entry, same
honest fills, same costs. The only variable is the index the filter reads.

The data is a random walk, so there is no edge to find. Whatever the naive pass
reports is lookahead, priced. Then the probe (`backtests/probes.py`) runs both
filters twice, once on the full session and once with the future cut off, and
shows it can catch the leak without anyone reading the code.

To run it for real: swap `synth_session` for `load_bars_csv` on your own 1-minute
data, and put your own higher-timeframe read into `prefix_invariance`.
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "backtests"))

from costs import FULL                    # noqa: E402
from data import synth_session            # noqa: E402
from kernels import honest_exit, validate_kernels  # noqa: E402
from probes import prefix_invariance      # noqa: E402

N_SESSIONS = 800
HTF = 10          # higher timeframe, in minutes
OR_MINUTES = 30   # opening range
FIXED_R = 5.0     # 1:1 bracket, stop and target 5 ES points (20 ticks) from entry
R_MULT = 1.0


def htf_direction(bars, honest: bool):
    """Per 1-minute bar: +1 if the filter's 10-minute candle is green, -1 red, None if none yet.

    Both versions build the 10-minute candles from the same 1-minute bars. They
    differ by one index, which is how this bug looks in real code.
    """
    out = []
    for i in range(len(bars)):
        block = i // HTF
        if honest:
            # last completed block. A block is finished only once its final minute
            # has closed, so from minute 0 to minute 8 of a block, it's the previous one.
            done = (i + 1) // HTF - 1
            if done < 0:
                out.append(None)
                continue
            lo, hi = done * HTF, done * HTF + HTF
        else:
            # the block this minute sits in, as it looks once the data is complete
            lo, hi = block * HTF, min(block * HTF + HTF, len(bars))
        o, c = bars[lo].open, bars[hi - 1].close
        out.append(1 if c > o else -1)
    return out


def filtered_orb(bars, honest: bool):
    """First opening-range breakout the 10-minute filter agrees with. One per session."""
    orh = max(b.high for b in bars[:OR_MINUTES])
    orl = min(b.low for b in bars[:OR_MINUTES])
    d = htf_direction(bars, honest)
    for i in range(OR_MINUTES, len(bars) - 1):
        c = bars[i].close
        if c > orh and d[i] == 1:
            return i, "long"
        if c < orl and d[i] == -1:
            return i, "short"
    return None


def trade_net(bars, i: int, side: str) -> float:
    """Next-bar entry, honest fills, full costs. Identical for both passes."""
    slip = FULL.slip_points()
    entry = bars[i + 1].open + (slip if side == "long" else -slip)
    stop = entry - FIXED_R if side == "long" else entry + FIXED_R
    target = entry + R_MULT * FIXED_R if side == "long" else entry - R_MULT * FIXED_R
    # honest_exit starts checking at entry_idx + 1. Pass the SIGNAL bar, so the first bar
    # checked is the entry bar itself: you got in at its open, and the rest of that minute
    # can stop you out like any other.
    reason, exit_price, _ = honest_exit(side, i, entry, stop, target, bars, "honest")
    if reason == "stop":
        exit_price -= slip if side == "long" else -slip
    pts = (exit_price - entry) if side == "long" else (entry - exit_price)
    return pts * FULL.point_value - FULL.commission_round_turn()


def _usd(x: float) -> str:
    return f"-${-x:,.0f}" if x < 0 else f"${x:,.0f}"


def main() -> None:
    validate_kernels()
    print()

    results = {"naive  (forming 10m)": [], "honest (last closed)": []}
    for seed in range(N_SESSIONS):
        bars = synth_session(seed)
        for label, honest in (("naive  (forming 10m)", False), ("honest (last closed)", True)):
            sig = filtered_orb(bars, honest)
            if sig:
                results[label].append(trade_net(bars, *sig))

    print(f"ORB + 10-minute trend filter on {N_SESSIONS} random-walk sessions (1 contract ES)")
    print("same entry, same fills, same costs. the only change: which 10-minute candle.\n")
    print(f"{'filter reads':<24}{'trades':>8}{'net $':>12}{'$/trade':>10}{'win rate':>10}")
    print("-" * 64)
    for label, rs in results.items():
        wr = sum(1 for r in rs if r > 0) / len(rs)
        print(f"{label:<24}{len(rs):>8}{sum(rs):>12,.0f}{sum(rs) / len(rs):>10.2f}{wr:>9.1%}")
    print("-" * 64)

    # The probe: no code reading. Run each filter on the whole session, then again
    # with every bar after i deleted, and compare the value at i.
    bars = synth_session(0)
    print("\nprobe: does the value at minute i change when the future is deleted?")
    for label, honest in (("naive ", False), ("honest", True)):
        rep = prefix_invariance(lambda b, h=honest: htf_direction(b, h), bars)
        verdict = "PASS" if rep["passed"] else "LEAK"
        print(f"  {label}  {verdict}  {len(rep['leaks'])} of {rep['checked']} minutes changed")
        if rep["leaks"]:
            i, full, cut = rep["leaks"][0]
            print(f"          first at minute {i}: full data says {full:+d}, "
                  f"what you'd have seen live says {cut:+d}")

    naive, honest = (sum(r) for r in results.values())
    print(f"\nthe data was random. the naive filter reported {_usd(naive)}; "
          f"the honest one {_usd(honest)}.")
    print("the strategy never changed. one index did. the probe caught it without "
          "reading a line of the code.")


if __name__ == "__main__":
    main()
