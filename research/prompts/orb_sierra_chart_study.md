# One-shot prompt — ORB signal study (Sierra Chart / ACSIL, C++)

Paste everything in the fenced block below into Claude Code (or any capable agent) to
regenerate the Sierra Chart Opening Range Breakout study from scratch. Every requirement
here encodes something that was hit and fixed during the original build — keep them all
and the study compiles and behaves on the first try.

Output one file: `sierra/studies/OPTD_Opening_Range.cpp`. Deploy and build it with
[`sierra/DEPLOY.md`](../../sierra/DEPLOY.md).

## Before you paste

**Give the agent Sierra Chart's own example source.** ACSIL has a small public corpus,
which is exactly the condition under which a model produces a plausible function that does
not exist. The cure is on your disk already: the `ACS_Source` folder inside your Sierra
Chart installation ships ~38 example files including `sierrachart.h`, `scconstants.h`,
`scstructures.h`, `scdatetime.h`, `Template.cpp` and `Studies.cpp` through `Studies8.cpp`.
It is the folder **Analysis → Build Custom Studies DLL** compiles from.

Add it as a readable working directory before you paste — in Claude Code:

```
/add-dir <path-to-your-SierraChart-install>/ACS_Source
```

The prompt below refers to that folder as `ACS_Source` and makes reading it a hard
requirement, including "if you cannot find the signature there, stop rather than invent
it."

## Why this prompt is shaped the way it is

Four requirements in it are correctness, not style. They are the difference between a
study that looks right and one that is right:

- **The bar-close gate.** Without `sc.GetBarHasClosedStatus() != BHCS_BAR_HAS_CLOSED`, the
  study re-evaluates the still-forming bar on every tick. A condition true on one tick is
  false two ticks later, and you get the classic symptom: the message log shows signals,
  the chart shows no arrows, the export shows zeros. Three places that should agree and
  none of them do.
- **Resetting persistent variables at `i == 0`.** `sc.GetPersistentInt`/`Float`/`Double`
  live in the chartbook and are *restored* on reload, not zeroed. Skip the reset and the
  study works on the first recalculation and emits nothing on every one after, because the
  "already fired" flags survive.
- **Subgraphs, not drawing tools.** Subgraphs reset naturally each day, survive a
  recalculation, and appear in Export Chart Data — which is how you verify the study
  later. Drawing tools need lifecycle management you don't want here.
- **Zero means "nothing here", with `DrawZeros = false`.** That is what stops one day's
  level line being dragged to zero and joined to the next day's.

And one that is scope: **a signal study is signals only.** No order API, not even
referenced. It has to stay verifiable on its own.

---

```
I want a Sierra Chart ACSIL custom study: an Opening Range Breakout signal study.
Signals only - it draws levels and marks signals. It must not place, modify, or manage
any order, and must not reference any sc.*Entry / sc.*Exit / order-related API at all.

=== REFERENCE MATERIAL - READ BEFORE YOU WRITE ANY CODE ===
Sierra Chart's own example source is in the ACS_Source folder I have given you access
to. It is the only reference you have and it is authoritative - prefer a pattern you
can point at in that folder over one you remember.

Read at minimum:
  - Studies6.cpp -> scsf_HighLowForTimePeriodExtendedLines
      The closest analogue that ships with the platform: high/low over a user time
      window, held across the rest of the session, reset each day. Study how it gets
      time-of-day inputs, how it compares bar timestamps to a window, and how it
      resets its running high/low at the day boundary.
  - Studies.cpp  -> scsf_SessionIndicator          (session detection)
  - Studies8.cpp -> scsf_TimeRangeHighlight        (time-of-day comparison)
  - Studies2.cpp or Studies8.cpp                   (any DRAWSTYLE_ARROW subgraph)
  - Template.cpp                                   (minimal study skeleton)
  - sierrachart.h / scconstants.h / scstructures.h / scdatetime.h
                                                   (signatures and constants)

=== THE RULE - stated so it has exactly one meaning ===
All times below are TIME OF DAY IN THE CHART'S TIMEZONE. Do not convert timezones.

  1. SESSION. The session runs from "Market Open Time" to "Session End Time" on each
     calendar trading day the chart contains.
  2. OPENING RANGE. The opening range window starts at Market Open Time and lasts
     "Opening Range Minutes". OR High = the highest high of every bar whose timestamp
     falls in that window. OR Low = the lowest low of the same bars. Build the range
     from HIGH and LOW, never from closes.
  3. RANGE COMPLETE. The range is complete at the first bar that closes at or after
     (Market Open Time + Opening Range Minutes). Before that moment the range is
     forming and NO signal may fire.
  4. LONG SIGNAL. After the range is complete and before Session End Time: count
     CONSECUTIVE closed bars whose CLOSE is strictly greater than OR High. When that
     count reaches "Confirmation Closes", fire a LONG signal on that bar.
  5. SHORT SIGNAL. Same, mirrored: consecutive closed bars whose CLOSE is strictly
     less than OR Low.
  6. RESET. A close back inside the range (close <= OR High and close >= OR Low)
     resets BOTH counters to zero. A close beyond one rail resets the opposite
     counter to zero.
  7. ONE PER SIDE PER SESSION. At most one long signal and one short signal per
     session. After a side has fired, that side is done for the day; the other side
     may still fire.
  8. NO SIGNAL outside the session, inside the opening-range window itself, at or
     after Session End Time, or on any bar that is not closed.
  9. NO RANGE, NO SIGNALS. If a session never produces a complete opening-range
     window - half day, holiday, missing data, the chart starts mid-session - that
     session produces no signals and no levels. Do not fall back to a partial range,
     and never carry yesterday's range into today.
 10. RISK LINES. On the bar a signal fires, compute and hold for the rest of the
     session:
        Risk = "Risk Points" if "Use OR Width As Risk" is No,
               otherwise Risk = OR High - OR Low.
        Long : Stop = signal bar close - Risk ; Target = signal bar close + Risk * "Target R Multiple"
        Short: Stop = signal bar close + Risk ; Target = signal bar close - Risk * "Target R Multiple"
     These are DRAWN LEVELS ONLY. Nothing is executed, nothing is tracked, there is
     no notion of the trade being hit, stopped, or closed. If Target R Multiple is 0,
     draw no target line.

=== INPUTS - every one of these is a user input, no constants in the logic ===
  Market Open Time            time input, default 09:30:00
  Opening Range Minutes       int,  default 30,  min 1,   max 600
  Session End Time            time input, default 16:00:00
  Confirmation Closes         int,  default 1,   min 1,   max 50
  Risk Points                 float, default 20.0, min 0
  Use OR Width As Risk        yes/no, default No
  Target R Multiple           float, default 2.0, min 0   (0 = no target line)
  Show Opening Range Lines    yes/no, default Yes
  Show Midline                yes/no, default Yes
  Show Stop/Target Lines      yes/no, default Yes
  Show Signal Arrows          yes/no, default Yes
  Log Signals To Message Log  yes/no, default No

=== OUTPUTS - use SUBGRAPHS, not drawing tools ===
Draw every level as a subgraph array, not with sc.UseTool. Subgraphs reset naturally
each day, survive a recalculation, and appear in Export Chart Data - which is how the
study gets verified later. Drawing tools need lifecycle management I do not want here.

  Subgraph 0  "OR High"   DRAWSTYLE_STAIR_STEP,  DrawZeros = false
  Subgraph 1  "OR Low"    DRAWSTYLE_STAIR_STEP,  DrawZeros = false
  Subgraph 2  "OR Mid"    DRAWSTYLE_STAIR_STEP,  DrawZeros = false
  Subgraph 3  "Long Signal"   DRAWSTYLE_ARROW_UP,   drawn at the bar's low
  Subgraph 4  "Short Signal"  DRAWSTYLE_ARROW_DOWN, drawn at the bar's high
  Subgraph 5  "Stop"     DRAWSTYLE_STAIR_STEP,  DrawZeros = false
  Subgraph 6  "Target"   DRAWSTYLE_STAIR_STEP,  DrawZeros = false

Level subgraphs carry their value on EVERY bar from the moment the range completes
through the last bar before Session End Time, so the line is continuous across the
session, then go to zero. Zero is the "nothing here" value and DrawZeros = false is
what keeps days from connecting to each other.

Signal subgraphs are non-zero on the signal bar only.

=== PLATFORM RULES - these are not style preferences, they are correctness ===
  A. BAR-CLOSE GATE. Use sc.AutoLoop = 1. Immediately after your early input reads,
     before any signal logic:
         if (sc.GetBarHasClosedStatus() != BHCS_BAR_HAS_CLOSED)
             return;
     Without it the study re-evaluates the forming bar on every tick, a condition can
     be true on one tick and false two ticks later, and you get the classic symptom:
     the message log shows signals, the chart shows no arrows, and the export shows
     zeros. Three places that should agree and none of them do. Note this gate does
     NOT block backfill - every bar except the single live forming one reports closed,
     including all historical bars during a full recalculation.
  B. PERSISTENT STATE RESET. Keep per-session state (OR high, OR low, the two
     consecutive counters, the two fired flags, the current session date, the held
     stop/target values) in sc.GetPersistentInt / sc.GetPersistentFloat /
     sc.GetPersistentDouble. These are stored in the chartbook and are RESTORED on
     reload, not zeroed. At i == 0, reset every one of them explicitly.
     Skip this and the study works on the first recalculation and emits nothing on
     every recalculation after.
  C. NO LOOKAHEAD. Only ever read bar index i and earlier. Never read i+1. The value
     you use to decide must be one that existed at the moment the bar closed.
  D. Do not read an SCInput inside the sc.SetDefaults block - it returns unset values
     there, and SetDefaults runs before the user's saved values are applied anyway.
     Read inputs in the runtime body.
  E. SetDefaults only runs the first time the study is attached. If you change a
     default, a color, or a draw style later, it will not appear until the study is
     removed and re-added. Say so in a comment.
  F. Detect the session-date rollover from the bar timestamps yourself and reset the
     session state there. Do not assume bar 0 is a session start, and do not assume
     any bar lands exactly on Market Open Time.
  G. If you need SCDateTime, SCString, subgraph, or input API you are not certain
     about, do not guess a signature. Find it in ACS_Source and say which file and
     function you took it from. If you cannot find it there, tell me and stop rather
     than inventing it.

=== FILE AND STYLE ===
  - One file: sierra/studies/OPTD_Opening_Range.cpp
  - #include "sierrachart.h" and SCDLLName("OPTD_Studies")
  - Study function scsf_OPTD_OpeningRange, sc.GraphName = "OPTD - Opening Range Breakout"
  - sc.GraphRegion = 0 (price panel), sc.AutoLoop = 1
  - Header comment: what the rule is, that it is signals only, and one line on the
    bar-close gate and why it is there.
  - Comment the non-obvious parts. Assume the reader has never written ACSIL and is
    going to read this file to learn from it.
  - ASCII only in any string that reaches the message log.

=== BEFORE YOU WRITE CODE ===
Do these three things first, in this order, and wait for me after step 3:
  1. Restate the rule back to me in your own words.
  2. List every place my description is still ambiguous, and what you would assume.
     Be specific - "what happens if a bar straddles Market Open Time" is useful,
     "edge cases" is not.
  3. Tell me which example files you read and which pattern you are taking from each.

=== ACCEPTANCE - how I will check it ===
  1. It compiles via Analysis > Build Custom Studies DLL with no errors.
  2. On a 1-minute chart with defaults, each day shows one OR High line, one OR Low
     line and a midline, starting when the range completes and running to the session
     end. No lines before the range completes. No line joining one day to the next.
  3. Opening Range Minutes 30 -> 5 changes where the lines start. Confirmation
     Closes 1 -> 5 makes signals later and rarer. Both without recompiling.
  4. I pick three signal bars by hand and check the arrow is on the bar where the
     rule first became true - not one bar early, not one bar late.
  5. Export Chart Data shows non-zero values in the level columns across the session
     and non-zero in a signal column only on signal bars. If the chart and the export
     disagree, rule A is wrong.
  6. A half day or a chart that starts mid-session shows no levels and no signals for
     that session.
```

---

## The ambiguities it will find (and how the shipped study resolves them)

Step 2 of the prompt exists because a rule stated in prose always has holes. These are the
ones that came back, and the answer baked into `sierra/studies/OPTD_Opening_Range.cpp`. If
you change the rule, revisit them.

| Ambiguity | How the shipped study answers it |
|---|---|
| **A bar straddling a boundary.** Sierra Chart timestamps an intraday bar at its **start** unless the chart has "Use Bar Ending Date-Time" on, so "every bar whose timestamp falls in the window" and "the first bar that closes at or after the window end" disagree. | Timestamp only, used consistently: in-window is `t >= open && t < end`; the range completes on the first bar with `t >= end`. Under the default that bar is the first one entirely past the window, so every contributing bar has fully closed — no lookahead. Bar-ending timestamps shift it one bar. |
| **"Chart starts mid-session"** — once built, a range from 09:45 looks identical to a real one. How does the study know? | A session is valid only if the **first bar seen on that calendar date** is timestamped at or before Market Open Time. A 24-hour chart passes; a day-session chart whose first bar is exactly the open passes; data beginning at 09:45 does not, and that session draws nothing. |
| **Both sides fire in one session** — there is one Stop subgraph and one Target subgraph. | The **most recent** signal owns the risk lines; a later short replaces the earlier long's. Visible as a step in the stair-step line. |
| **Market Open Time >= Session End Time** (an overnight session). | Not supported, and not special-cased: the range simply never completes inside the session, so rule 9 already produces nothing. |
| **`Use OR Width As Risk` with a one-tick range.** | The stop is drawn on the close. Degenerate, but not silently suppressed. |
| **Display toggles vs. logic.** | The `Show ...` inputs only suppress drawing. Counters, fired flags and the message log are unaffected, so toggling display never moves a signal. |
| **Half day.** | A half day that opens on time completes its range normally and does get signals. Only a session whose data ends before the window closes produces nothing. |
| **Rule B says reset at `i == 0` "and return".** | The shipped study resets all persistent state at `i == 0` but then **processes bar 0** instead of returning. On a day-session-only chart bar 0 *is* the 09:30 bar — the first opening-range bar and the evidence the session start was seen — so returning would silently kill day one. The reset, which is what rule B is actually about, is unchanged. |
