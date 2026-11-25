# Size to the market before the open: the VIX sizing check prompt (v1)

Ships with video 16, [How to Size Trades in a Volatile Market (Position Sizing With the VIX + Claude Code)](https://youtu.be/9ueH5JAdfPM).
One prompt for plain Claude Code. It builds a small Python script you run once before the open. The script pulls
the free daily VIX and VXN history from Cboe, measures how far the VIX has jumped above its own 20-day average,
and tells you how many contracts your risk buys at today's ATR.

**What it gets you:** one line before the open: the tier (NORMAL / CAUTION / STRESS), the jump (today's close ÷
its 20-day average), the expected daily move (VIX ÷ 16), and your contract count, rounded down.

**What it does not get you:** a direction, a signal or an edge. It says how big the day might be, not which way
it goes. Sizing down is risk control: it also shrinks the rebound when the market rips back (the video's Monday).
It never touches orders. Your ATR comes from your own chart, and your risk numbers are yours, not the video's.

## How to use it

1. Make an empty folder and open Claude Code in it.
2. Paste the prompt below as-is.
3. Fill `config.json` with your own numbers, or just tell Claude Code in plain words ("I trade MNQ, I risk $200,
   it's $2 a point") and let it write the file. You don't have to code anything.
4. Each morning, paste today's 14-day ATR from your chart into `config.json` and run the script.
5. Read it against your plan. A CAUTION or STRESS day means your usual stop is a smaller piece of the day than
   you think, so the contract count is what moves, not the stop.

## The prompt

This is the prompt typed on screen in the video, word for word (the Cboe link is written out in full here).

```
Build me a small Python script I can run before the open:
1. Download daily VIX and VXN closes from Cboe's free history CSVs (https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv, same for VXN). Send a browser User-Agent and follow redirects.
2. Compute the latest close divided by the 20-day simple average of the last 20 closes, including the latest one (the "jump"), and the expected daily move % = close / 16.
3. Read my settings from config.json: which index (VIX or VXN), my risk per trade in $, my stop as a fraction of ATR, $ per point, and today's 14-day ATR in points (I'll paste it from my chart).
4. Contracts = floor(risk / (stop x ATR x $ per point)). If that's 0, say so; never round up.
5. Tier on the jump: under 1.10 = NORMAL, 1.10-1.25 = CAUTION, 1.25+ = STRESS ("ATR is probably too small today").
6. Print one line: tier, jump, expected move, contracts.
It must never place, change or cancel orders. Read-only, informational.
```

## The config from the video (example values)

Claude Code names the keys its own way; these are the ones on screen. **Example values, not a recommendation.**

```json
{
  "index": "VXN",
  "risk_dollars": 200,
  "stop_atr_fraction": 0.5,
  "dollars_per_point": 2,
  "atr14_points": 985
}
```

- `index`: VIX is built from S&P 500 options, VXN from Nasdaq-100 options. For NQ the video uses VXN (over 18
  years it lined up with NQ's range a little better than VIX did, but it's close). For ES, VIX.
- `dollars_per_point`: MNQ $2, NQ $20, MES $5, ES $50.
- With these exact numbers the script prints **0 contracts**: $200 ÷ (0.5 × 985 × $2) = 0.2. That's the check
  doing its job: on a 985-point ATR day, half an ATR on one micro costs about $985, so a $200 risk doesn't buy it.
  It says 0 instead of rounding up to 1.

## Read it against the video

| What the script prints | Where the video explains it |
|---|---|
| Expected move = VIX ÷ 16 | "What the VIX tells you" (0:49). 16 ≈ √252 trading days. VIX 15 ≈ a 0.9% day, VIX 36 ≈ 2.25% |
| Why the tiers sit on the jump, not the level | "The jump" (3:33). VIX ≥ 25% above its 20-day average: 1 NQ day in 4 ran past 1.5 ATR, against 1 in 37 when it sat 10%+ below. The forecast that used the jump was built on 2009–2019 and checked on 2020 → now |
| NORMAL / CAUTION / STRESS | "The build" (4:57). Under 1.10 / 1.10–1.25 / 1.25+ |
| Contracts, never rounded up | "Same stop, less room" (2:45). Keep the stop as a piece of ATR; let the contract count change |
| What it can't do | "Two honest things" (10:52). Risk control, not an edge |

## Versions

- **v1** (2026-11-25): as typed in the video.
