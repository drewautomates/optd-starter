# One-shot prompt — ORB indicator + strategy (Pine Script v6)

Paste everything in the fenced block below into Claude Code (or any capable agent) to regenerate **both** the indicator and the paired strategy from scratch. Every requirement here encodes a gotcha that was hit and fixed during the original build — keep them all and the scripts compile and trade on the first try.

Output two files in `indicators/pine_reference/`:
- `Opening_Range.pine` (indicator)
- `Opening_Range_Strategy.pine` (strategy)

---

```
Build TWO TradingView Pine Script v6 files: an Opening Range Breakout (ORB) INDICATOR and a paired STRATEGY. Author tag: OPTD. Both must share an identical signal engine so they stay in parity.

=== SHARED INPUTS (same in both files) ===
- Opening Range Time (EST): input.session, default "0930-1000". Window that BUILDS the range.
- Regular Session Time (EST): input.session, default "0930-1600". Window the levels DISPLAY across; the strategy also flattens at its end.
- Timezone: input.string, default "America/New_York" (options: New York, Chicago, Los Angeles, UTC).
- Signal timeframe: input.timeframe, default "1". The timeframe the range AND the breakout counter are computed on — INDEPENDENT of the chart timeframe, so swapping the chart view does not change the signal.
- Consecutive closes outside range for signal: input.int, default 1 (1..50). Number of CONSECUTIVE signal-timeframe closes beyond ORH/ORL to trigger. A close back inside resets the counter.

=== OR LEVELS — computed INLINE on the chart timeframe (identical in both files) ===
- inOR  = not na(time(timeframe.period, orSess, tz)); inRTH likewise for rthSess.
- Detect orOpen (first OR bar), orClose (first bar after OR), newDay (first RTH bar).
- Build the range from HIGH/LOW, INLINE on the chart (NOT through request.security): on orOpen set orH=high, orL=low, orDone=false; while inOR, orH=max(orH,high), orL=min(orL,low). On orClose set orDone=true. On (newDay and not inOR) clear orH/orL to na (so yesterday's range doesn't linger before today's OR rebuilds). orM=(orH+orL)/2.
  CRITICAL: the OR high/low are TIMEFRAME-INVARIANT — the highest high over a clock window is the same number on 1m or 30m bars — so compute them INLINE. Pulling the LEVELS through request.security causes day-boundary forward-fill lag, a zero-width "snap"/immediate-drop at the OR open, and makes the indicator and strategy draw DIFFERENTLY when both are on the chart. Inline = smooth, daily-resetting, and identical across the two scripts.
  CRITICAL: build from HIGH/LOW, not closes — a close-based range collapses to ORH==ORL (zero width) when the OR window spans only one signal-TF bar (e.g. a 30m signal TF on a 30-minute OR).

=== SIGNAL COUNTER — the ONLY timeframe-dependent piece (on the signal TF) ===
- A small function f_count() recomputes the SAME OR window in its own context and returns the consecutive-close COUNTS [up, dn]: reset up/dn on orOpen/newDay; only while inRTH and orDone and orH not na: close>orH -> up+=1,dn:=0 ; close<orL -> dn+=1,up:=0 ; else up:=0,dn:=0.
  CRITICAL: return the COUNTS, not momentary booleans — a one-bar `true` does not survive the request.security boundary reliably. Detect the edge on the chart side.
- A request.security signal TF must be >= the chart TF. Clamp if the chart is coarser:
    sigSecs = timeframe.in_seconds(sigTF); chartSecs = timeframe.in_seconds(timeframe.period);
    tfClamped = chartSecs > sigSecs; effTF = tfClamped ? timeframe.period : sigTF.
- [upCount, dnCount] = request.security(syminfo.tickerid, effTF, f_count(), lookahead=barmerge.lookahead_off)  // non-repainting.
- Detect the breakout edge LOCALLY on the chart (using the inline orH/orL/orDone):
    breakUp = not na(orH) and orDone and upCount >= nCloses and (na(upCount[1]) or upCount[1] < nCloses)
    breakDn = not na(orL) and orDone and dnCount >= nCloses and (na(dnCount[1]) or dnCount[1] < nCloses)
- Show an on-chart warning label (on barstate.islast) when tfClamped is true: "Chart TF coarser than Signal TF — signal computed on chart TF. Lower the chart timeframe for a finer signal."

=== INDICATOR (Opening_Range.pine) ===
- overlay=true. Title "OPTD — Opening Range (ORB)".
- Plot ORH/ORL/ORM with style=plot.style_linebr, gated to display only during the chart's view of the regular session (so days don't connect and lines reset daily). Default colors: ORH blue (#2962ff), ORL pink (#e91e63), ORM white. Toggle for midline, range fill (fill between ORH/ORL with transparency), and price-scale labels.
- plotshape breakUp (triangleup below bar, "OR↑") and breakDn (triangledown above bar, "OR↓"), behind a "Show breakout markers" toggle.
- alertcondition for breakUp and breakDn.
- Expose ORH/ORL/ORM in the status line (plotchar display=display.status_line).

=== STRATEGY (Opening_Range_Strategy.pine) ===
- Title "OPTD — Opening Range (ORB) Strategy". overlay=true.
- strategy() header MUST include: default_qty_type=strategy.fixed, default_qty_value=1, pyramiding=0, calc_on_every_tick=false, commission_type=strategy.commission.cash_per_contract, commission_value=2.50, slippage=2, initial_capital=50000, margin_long=5, margin_short=5.
  CRITICAL: margin_long/short=5 is REQUIRED for futures. With the default (0) the emulator demands the FULL notional in cash (~$600k for 1 NQ contract), so a $50k account places ZERO trades and the tester shows "This report requires trade data". Margin does not affect per-trade P&L.
- Inputs: Direction (Both / Long only / Short only); Stop (R = OR width), float default 1.0; Target (R multiple), float default 2.0 (0 = no target, session exit only); Max one trade per session (bool, default true); Flatten at end of session (bool, default true).
- RISK MODEL — R = opening-range width, anchored to the breakout RAIL (timeframe-stable, independent of the entry close):
    R = orH - orL
    Long : stop = orH - stopR*R (stopR=1 => orL), target = rTarget>0 ? orH + rTarget*R : na
    Short: stop = orL + stopR*R (stopR=1 => orH), target = rTarget>0 ? orL - rTarget*R : na
- Gates: a one-trade-per-session latch reset on the chart's first RTH bar; direction filter; require not na(orH) and R>0.
- Execution: on breakUp/breakDn -> strategy.entry then strategy.exit(stop=..., limit=...). Flatten with strategy.close_all on the first bar after the regular session when "Flatten at end of session" is on.
- Plot ORH/ORL/ORM (linebr, RTH-gated) and the same OR↑/OR↓ markers for visual parity with the indicator.

=== HEADER COMMENT (both) ===
Include a short header explaining the timeframe-stable design and a one-line note that the TradingView Strategy Tester is a first sniff, not proof.

=== TEST EXPECTATIONS ===
- 1m chart on NQ1!/ES1!/MNQ1!, Signal TF 1, N=1 -> a trade most days; tester populates.
- Signal TF 5 or 30 -> a real (non-collapsed) range; signal locked to that TF.
- Chart TF coarser than Signal TF -> orange warning label, signal clamps to chart TF.
```

---

## Why each gotcha matters (cheat sheet for the walkthrough)

| Symptom | Cause | Fix in the prompt |
|---|---|---|
| Range collapses to one line on coarse signal TF | Close-based range, OR window = 1 signal bar → ORH==ORL | Build range from **high/low** |
| Markers show but **no trades** in tester | Momentary `true` lost across `request.security` | Return **counts**, detect edge on chart side |
| Signal moves when you change chart TF | Counter logic ran on chart TF | Compute the **counter** on a fixed Signal TF |
| Blank chart / no signal on high TF | `request.security` can't see finer closes from a coarser chart | **Clamp** effTF + warn |
| Range draws "weird" / **immediate drop** on TF mismatch; indicator ≠ strategy | LEVELS pulled through `request.security` (forward-fill lag, zero-width snap) | Compute **levels INLINE** on the chart (they're TF-invariant); only the counter uses security |
| "This report requires trade data" | Futures notional ($600k) > capital ($50k); orders rejected | `margin_long/short = 5` |
