"""The fills demo — naive vs honest, on pure random data.

Run:  python backtests/runs/run_fills_demo.py

Random-walk sessions have NO real edge. So an honest backtest must report ~0
expectancy. Anything the *naive* fills report above that is manufactured — phantom
profit conjured by assuming the target filled whenever stop and target shared a bar.

This runs the same ORB strategy through both fill models and shows the gap.

To run it for real: point `load_bars` at your own tick data (or, on the desk, the
private Sierra Chart .scid adapter) instead of `synth_session`. Same code, real fills.
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "backtests"))
sys.path.insert(0, os.path.join(ROOT, "indicators", "python"))

from data import synth_session            # noqa: E402
from kernels import honest_exit, validate_kernels  # noqa: E402
from orb import orb_signals               # noqa: E402

N_SESSIONS = 800


def _stats(rs: list[float]) -> dict:
    n = len(rs)
    wins = [r for r in rs if r > 0]
    losses = [r for r in rs if r <= 0]
    gross_win = sum(wins)
    gross_loss = abs(sum(losses))
    pf = (gross_win / gross_loss) if gross_loss > 0 else float("inf")
    return {"n": n, "win_rate": (len(wins) / n if n else 0.0),
            "expectancy_R": (sum(rs) / n if n else 0.0), "pf": pf, "total_R": sum(rs)}


def main() -> None:
    # the kernel proves itself honest before we trust a single number
    validate_kernels()
    print()

    naive_R: list[float] = []
    honest_R: list[float] = []
    phantom_wins = 0          # trades naive books as wins that honest books as losses

    for seed in range(N_SESSIONS):
        bars = synth_session(seed)
        # tight 1:1 bracket: on random data the TRUE expectancy is provably 0,
        # so any naive edge is unambiguously the fills lie, not the strategy.
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

    print(f"ORB on {N_SESSIONS} random-walk sessions  ({sn['n']} trades)\n")
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
    print("the data was random. the honest edge is ~0. everything above it was the fills.")


if __name__ == "__main__":
    main()
