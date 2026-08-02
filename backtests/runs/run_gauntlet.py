"""The gauntlet — all three tests, end to end.

Run:  python backtests/runs/run_gauntlet.py

Three lies every backtest tells you, and the test that catches each one:

  1 · FIT    let it cheat. If it still loses with every advantage a backtest
             can fake, you're done — nothing else needs checking.
  2 · FILL   interrogate it. When your stop and your target land inside the
             same bar, how does it decide which hit first? If it can't answer,
             it's guessing, and it's guessing in your favour.
  3 · FLUKE  take the signal away. Same times in, same times out, no signal.
             If you can't beat that, you don't have a strategy.

Everything here runs on synthetic random-walk data, on purpose. Random data has
no edge in it, so every dollar these tests report as profit is *provably* fake —
you get to watch each bias manufacture money and then hand it back. That's the
lie, in a lab, where you can see all of it.

Then you point the same three tests at your own results and find out which one
yours dies to.

Run them individually for the full output:
    python backtests/runs/run_cheat_demo.py
    python backtests/runs/run_fills_demo.py
    python backtests/runs/run_drift_demo.py
"""

from __future__ import annotations

import os
import runpy
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))

# Output is deliberately plain ASCII: these scripts have to run identically on a
# Windows console with a legacy code page, where a stray em dash is a crash.
TESTS = [
    ("1 - FIT",   "run_cheat_demo.py", "let it cheat, see if it still loses"),
    ("2 - FILL",  "run_fills_demo.py", "naive vs honest same-bar resolution"),
    ("3 - FLUKE", "run_drift_demo.py", "take the signal away"),
]


def main() -> None:
    print("=" * 68)
    print("  THE GAUNTLET -- three lies, three tests, on provably edgeless data")
    print("=" * 68)

    started = time.time()
    failed: list[str] = []

    for label, script, blurb in TESTS:
        print(f"\n\n{'#' * 68}")
        print(f"#  TEST {label}  --  {blurb}")
        print(f"{'#' * 68}\n")
        path = os.path.join(HERE, script)
        try:
            runpy.run_path(path, run_name="__main__")
        except Exception as exc:                        # noqa: BLE001
            # Keep going — a gauntlet that stops at the first failure tells you
            # less than one that reports all three.
            print(f"\n!! {script} failed: {exc.__class__.__name__}: {exc}")
            failed.append(script)

    print(f"\n\n{'=' * 68}")
    if failed:
        print(f"  {len(failed)} of {len(TESTS)} tests did not complete: "
              f"{', '.join(failed)}")
    else:
        print(f"  all {len(TESTS)} tests ran  ({time.time() - started:.0f}s)")
    print("=" * 68)
    print("""
  The data was random. There was never an edge to find. Every number
  above zero came from a bias, not a strategy.

  Now point these at your own backtest. Run them before you put money
  behind it, not after.
""")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
