"""SCID reader demo — read the ticks, reconstruct the bars, see where honesty comes from.

Run:  python backtests/runs/run_scid_demo.py

Two acts:
  1. Write a synthetic `.scid`-shaped tick file, read it back by parsing the bytes, and
     reconstruct 1-minute bars from the ticks — deriving `up_first`, the bit OHLC throws
     away.
  2. Run those tick-reconstructed bars straight through the honest-vs-naive fills test.
     The data is a random walk, so the honest edge is ~0 and any naive edge is the fills
     lie — the same lesson as `run_fills_demo.py`, now anchored on the tick reading that
     makes honest fills possible in the first place.

To run it for real: point the reader at real `.scid` files (the private desk adapter)
instead of the synthetic writer. Same bars-from-ticks interface, real ticks.
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "backtests"))
sys.path.insert(0, os.path.join(ROOT, "indicators", "python"))

from kernels import honest_exit, validate_kernels        # noqa: E402
from orb import orb_signals                               # noqa: E402
from ticks import (bars_from_ticks, read_scid_like,       # noqa: E402
                   synth_ticks, write_scid_like)

N_SESSIONS = 1500
TICK_DIR = os.path.join(ROOT, "data", "tick")             # gitignored


def _stats(rs: list[float]) -> dict:
    n = len(rs)
    wins = [r for r in rs if r > 0]
    gross_win = sum(wins)
    gross_loss = abs(sum(r for r in rs if r <= 0))
    pf = (gross_win / gross_loss) if gross_loss > 0 else float("inf")
    return {"n": n, "win_rate": (len(wins) / n if n else 0.0),
            "expectancy_R": (sum(rs) / n if n else 0.0), "pf": pf, "total_R": sum(rs)}


def act1_read_a_scid_file() -> None:
    print("== act 1: read a .scid-like tick file ==\n")
    os.makedirs(TICK_DIR, exist_ok=True)
    path = os.path.join(TICK_DIR, "demo.scid")

    ticks = synth_ticks(seed=0)
    nbytes = write_scid_like(path, ticks)
    got = read_scid_like(path)                 # parse the bytes back — the actual skill
    # timestamps roundtrip exactly; prices are float32 on disk (faithful to .scid), so
    # they come back within sub-cent tolerance, not bit-identical.
    assert len(got) == len(ticks), "roundtrip count mismatch"
    assert all(g.t_us == t.t_us and abs(g.price - t.price) < 0.01
               for g, t in zip(got, ticks)), "roundtrip mismatch"

    print(f"wrote {len(ticks):,} synthetic ticks -> {os.path.relpath(path, ROOT)} "
          f"({nbytes / 1024:.1f} KB)")
    print("header: magic=SCID  header=56B  record=40B   |   "
          f"records read back = {len(got):,}")
    print("first ticks off the wire:")
    for t in got[:3]:
        print(f"    t=+{t.t_us / 1e6:6.2f}s   price={t.price:8.2f}   vol={t.volume}")

    bars = bars_from_ticks(got)
    b0 = bars[0]
    print(f"\nreconstructed {len(bars)} one-minute bars from {len(got):,} ticks")
    print(f"    bar 0:  O={b0.open:.2f}  H={b0.high:.2f}  L={b0.low:.2f}  C={b0.close:.2f}"
          f"   up_first={b0.up_first}")
    print("    ^ up_first — did the high print before the low? — is read straight off the")
    print("      tick order. An OHLC feed cannot tell you this. The fills kernel needs it.\n")


def act2_why_it_matters() -> None:
    print("== act 2: run the tick-reconstructed bars through honest vs naive fills ==\n")
    validate_kernels()
    print(f"\nrebuilding bars from ticks across {N_SESSIONS:,} sessions (~15s)...\n")

    naive_R: list[float] = []
    honest_R: list[float] = []
    phantom_wins = 0

    for seed in range(N_SESSIONS):
        bars = bars_from_ticks(synth_ticks(seed))     # ticks -> bars, every session
        for tr in orb_signals(bars, r_mult=1.0, fixed_r=1.0):
            _, _, rn = honest_exit(tr["side"], tr["entry_idx"], tr["entry"],
                                   tr["stop"], tr["target"], bars, "naive")
            _, _, rh = honest_exit(tr["side"], tr["entry_idx"], tr["entry"],
                                   tr["stop"], tr["target"], bars, "honest")
            naive_R.append(rn)
            honest_R.append(rh)
            if rn > 0 and rh <= 0:
                phantom_wins += 1

    sn, sh = _stats(naive_R), _stats(honest_R)
    naive_win_ct = sum(1 for r in naive_R if r > 0)

    print(f"ORB on {N_SESSIONS} random-walk sessions, bars rebuilt from ticks "
          f"({sn['n']} trades)\n")
    print(f"{'metric':<16}{'NAIVE fills':>16}{'HONEST fills':>16}")
    print("-" * 48)
    print(f"{'win rate':<16}{sn['win_rate']:>15.1%}{sh['win_rate']:>16.1%}")
    print(f"{'expectancy (R)':<16}{sn['expectancy_R']:>16.3f}{sh['expectancy_R']:>16.3f}")
    print(f"{'profit factor':<16}{sn['pf']:>16.2f}{sh['pf']:>16.2f}")
    print(f"{'total R':<16}{sn['total_R']:>16.1f}{sh['total_R']:>16.1f}")
    print("-" * 48)
    pct = (phantom_wins / naive_win_ct) if naive_win_ct else 0.0
    print(f"\nphantom wins: {phantom_wins} of {naive_win_ct} naive wins ({pct:.0%}) were "
          f"actually losses once fills were honest.")
    print("the ticks are where the intrabar truth lives. throw them away and your fills")
    print("become fiction — which is exactly the edge the naive column just made up.")


def main() -> None:
    act1_read_a_scid_file()
    act2_why_it_matters()


if __name__ == "__main__":
    main()
