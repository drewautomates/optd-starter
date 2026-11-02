# risk/ — size against the drawdown, not the account

The risk half of the method, from video 11 ([Why You Keep Busting Lucid and Topstep Accounts](https://youtu.be/KDV_R3aQcnA)).

| File | What it is |
|---|---|
| [`rope_calculator.xlsx`](rope_calculator.xlsx) | The rope calculator. Enter your max loss, your room right now and your size; it gives points to bust at every contract count (minis next to micros), the most contracts that survive a given move, how many normal-range days the rope holds, whether your daily limit fires before the max-loss line, and an illustrative ratchet ladder. Every output is a formula. Opens in Excel, or in Google Sheets via File → Import. |
| [`FLOOR-AND-RATCHET-CHECKLIST.md`](FLOOR-AND-RATCHET-CHECKLIST.md) | The one-page setup: size from the rope, a daily floor in code, a ratchet by hand, the day after a payout. |

Web version, with firm presets that link each figure to the firm's own rules page: [onepersontradedesk.com/tools/prop-firm-position-size-calculator](https://onepersontradedesk.com/tools/prop-firm-position-size-calculator).

The math: points to bust = room ÷ (contracts × $ per point). Touching the max-loss line is a bust, so 5 NQ on a $4,500 rope bust on exactly 45 points (5 × 45 × $20), and the most NQ that survive a 45-point move is 4.

Synthetic math, no strategy, no signals. Education, not advice. Practice on SIM.
