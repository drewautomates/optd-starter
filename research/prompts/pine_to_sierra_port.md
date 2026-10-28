# Pine Script → Sierra Chart port: the starter prompts (v1)

Ships with video 12, [How to Reverse Engineer Any TradingView Indicator (I Ported the Most Popular One)](https://youtu.be/VIDEO_ID).
Two prompts: the **port prompt** (Pine Script source → a Sierra Chart ACSIL study) and the **compare prompt**
(both exports → a bar-by-bar verdict). These are the same steps the video runs through an app, written for
plain Claude Code.

**What it gets you:** a `.cpp` study that compiles in Sierra Chart, a written map of every input and output,
and a verdict on whether the port actually matches the original.

**What it does not get you:** permission. Read the indicator's license before you port it. Most open-source
TradingView scripts are non-commercial and share-alike, and those terms carry over to your port. Never sell
or redistribute a port of someone else's script. Invite-only and paid scripts: leave them alone.

## How to use it

1. Copy the indicator's Pine Script source into a file in your project, e.g. `ports/<name>/source.pine`.
2. Export the chart from TradingView (Export chart data, time format **UNIX timestamp**). Scroll back first:
   it only exports what's loaded. Save it as `ports/<name>/tv.csv`.
3. Open Claude Code in your project and give it Sierra Chart's own examples: `/add-dir <your Sierra install>/ACS_Source`.
4. Paste the **port prompt** below. Answer what it asks, then build the study in Sierra Chart (see
   [`sierra/DEPLOY.md`](../../sierra/DEPLOY.md)). Build errors go straight back to Claude Code.
5. Add the study to the same symbol and timeframe, export it (Chart → Write Bar and Study Data To File,
   include hidden subgraphs) and paste the **compare prompt** with both files.
6. RED? Ask it to look at the first bar that fails on both sides, fix the `.cpp`, rebuild, re-export, compare again.

Looking right on the chart is not a verdict. Only the bar-by-bar comparison is.

## The port prompt

```text
Port this TradingView indicator to a Sierra Chart ACSIL study. The Pine Script source is in
ports/<name>/source.pine and a TradingView export of it is in ports/<name>/tv.csv.

Before any code:
1. Read the license at the top of the source. If it forbids what I'm doing, stop and tell me.
2. Use the Sierra Chart ACS_Source folder I added as the ONLY authority for ACSIL names and
   signatures. If a function or field isn't in ACS_Source, don't use it. Say so and stop.
3. Check the export: columns, bar count, time format, and the first non-empty bar of each column
   (that's the warm-up). Under 2,000 bars, tell me to export more.

Inventory, in writing, before you port: every input (name, type, default), every series in execution
order with its formula, every piece of state that persists between bars, every output with its title,
every built-in function whose seeding differs from Sierra's, and anything that repaints or looks ahead.
Port the code as written, not the intent. Flag anything that looks like a bug in the original.

Show me this table before writing the .cpp: TradingView output → Sierra subgraph index (0-based) →
SG number in the UI (1-based) → draw style. One subgraph per series I could backtest: every value,
every state (+1/-1), every event (non-zero on the bar it happens). Drawings are display only.

Code rules: #include "sierrachart.h" then SCDLLName(...) near the top; (std::max)(a, b); inputs in the
source's order with its defaults; sc.ValueFormat >= 4 on value subgraphs; sc.DataStartIndex at the first
valid bar. Keep persistent state behind sc.GetPersistentPointer, process closed bars only, reset on
sc.IsFullRecalculation and free it on sc.LastCallToFunction.

Then write ports/<name>/<name>.cpp and a map.json (TradingView column → Sierra column), and tell me
exactly which subgraphs to make visible and the export settings to use. Don't build it; I build it in
Sierra Chart and come back with a build error or the Sierra export.
```

## The compare prompt

```text
I have two exports of the same chart: a TradingView CSV (time in Unix seconds) and a Sierra Chart
"Write Bar and Study Data To File" text export. Same symbol, session and timeframe.

1. Load both. Convert both timestamps to UTC and line the bars up by bar open time. Tell me how many
   bars overlap and how many are in only one file.
2. Check prices first: open, high, low, close on every overlapping bar. Report % identical and the
   first 5 bars that differ. If prices don't match, stop and tell me why (session, timezone, roll,
   timeframe). The data has to match before the indicator means anything.
3. Map each indicator column in the TradingView file to its subgraph in the Sierra file. List any
   column you can't map.
4. For each mapped pair: % of bars that agree (within 1e-6, or 1 tick for price levels), the first
   10 bars that don't, and for signal columns whether they fire on the same bar.
5. Verdict: GREEN (prices identical, values agree on ≥99% of bars, signals on the same bars),
   RED (say which), or INCONCLUSIVE (nothing to compare, e.g. the indicator only draws).
Write it as a Python script I can rerun, then run it.
```

## No source code?

Closed-source but free: export the CSV on three or more timeframes, take screenshots of every setting, and
keep one symbol back. Ask Claude Code to form a hypothesis from the inputs, fit it on the in-sample files,
freeze it, then test it on the held-back file. Report the exact-match rate both ways. A formula that only
fits in-sample isn't found. Expect "very close", not exact.

## Read it against the video

| Video | What you see | Where it is here |
|---|---|---|
| 0:57 | Step 1: pick the indicator. Open source, free but closed, or invite-only (leave those alone) | "What it does not get you" + "No source code?" |
| 1:25 | Step 2: export the TradingView chart (scroll back first, time format Unix) | How to use it, step 2 |
| 2:17 | Step 3: Claude Code ports Pine Script to Sierra Chart C++ | The port prompt |
| 2:40 | Copy into `ACS_Source`, build, add the custom study | How to use it, step 4 + [`sierra/DEPLOY.md`](../../sierra/DEPLOY.md) |
| 3:33 | Export Sierra Chart and compare it against TradingView | The compare prompt |
| 7:50 | "If you don't have an app like this, the prompt does the same steps in Claude Code" | This file |
| 8:45 | Bar data first, then every indicator bar by bar | Compare prompt, steps 2 and 4 |
| 9:40 | One zone missing on Sierra Chart: ~80–90% there, then iterate | How to use it, step 6 |
| 11:04 | No source code: export several timeframes, add screenshots of every setting | No source code? |

The app in the video is my own workflow, not part of this repo. The port it makes of LuxAlgo's Smart Money
Concepts isn't here either: its license is non-commercial share-alike and the port is an example, not a product.

## Build errors you'll hit

The port prompt's code rules each exist because of one: `(std::max)` sidesteps the Windows `max` macro,
and `SCDLLName` near the top is what Sierra Chart scans for. The rest, with fixes, are in
[`sierra/DEPLOY.md` → The four things that strand people](../../sierra/DEPLOY.md#the-four-things-that-strand-people).
The one that costs the most time: you change a default and nothing happens. Remove the study and re-add it.

## Versions

- **v1** (2026-10-27): port prompt, compare prompt, the no-source lane.
