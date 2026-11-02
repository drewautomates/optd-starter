# Floor and ratchet checklist

From video 11, [Why You Keep Busting Lucid and Topstep Accounts (It's Not Your Strategy)](https://youtu.be/KDV_R3aQcnA).
Three things, and only one of them is code: **floor in code, ratchet in your hands, micros not minis.**

Education, not advice. Set all of this up on SIM first and run it until it's boring.

---

## 1 · Size against the drawdown, not the account

- [ ] Write down your firm's max loss and its type (end-of-day trailing, intraday trailing, static). Take it from the firm's own rules page, not a review site. Rules change.
- [ ] Write down your **room right now**: balance minus the max-loss line. That's your rope, not the max loss.
- [ ] Pick the adverse move you need to survive in points. Pick it from your own read of a normal session, not a crash.
- [ ] Open [`rope_calculator.xlsx`](rope_calculator.xlsx) (or the [web version](https://onepersontradedesk.com/tools/prop-firm-position-size-calculator)) and find the most contracts that survive that move.
- [ ] If that number is under 1 mini, trade micros. A micro is a tenth of the dollars per point, so the same setup gets ten times the points.
- [ ] The firm's max position is a ceiling, not a target.

## 2 · Floor in code

- [ ] Set a hard daily loss limit **in the platform or in your own code**, with a lockout. Not a number you hold in your head.
- [ ] Check it fires before the max-loss line does (the "daily floor check" in the sheet). If your daily limit is as wide as your rope, it can't save the account.
- [ ] When it hits, the day is over. No re-enabling, no "one more".
- [ ] Test the lockout on SIM: put on a trade, let it hit the floor, confirm the platform actually stops you.

## 3 · Ratchet in your hands

- [ ] Pick a rung size (the sheet's ladder is illustrative). Each rung of profit lifts the day's floor one rung, starting at breakeven.
- [ ] Write the ladder on a sticky note where you can see it while you trade.
- [ ] The ratchet stays manual on purpose. The floor protects the account. The ratchet trains the trader.
- [ ] Hit the ratchet floor and you're done for the day. Don't argue with it.

## 4 · The day after a payout

- [ ] After a payout, recompute your room. The payout pulls the cushion out, so the line is closer than it's ever been.
- [ ] Re-run the sheet with the new room and trade that size, not last week's.
- [ ] Trade smaller than you want to. That's the day you'll feel best and have the least buffer.

## 5 · Look at your own trades

- [ ] Journal every day: size, max adverse move, where you stopped managing the trade.
- [ ] Look for the pattern that only shows up written down (mine was green to red: up, stop managing, wait for it to come back).
- [ ] If the pattern is about you, not the setup, a new strategy won't fix it.
