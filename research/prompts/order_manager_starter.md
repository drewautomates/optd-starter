# Order manager — the starter prompt (v1)

Ships with video 7, **Sierra Chart Automated Trading: How to Build a System That Doesn't Blow Up (Claude Code)**.
This is the prompt shown full-frame at the end of that video, verbatim. Not a sanitised version.

**What it gets you:** a Sierra Chart ACSIL study that takes the signal from
[`sierra/studies/OPTD_Opening_Range.cpp`](../../sierra/studies/OPTD_Opening_Range.cpp) and places
and manages one bracketed trade in SIM, with an arming switch that defaults to OFF.

**What it does not get you:** a study you should turn on. That part is the four stages the video
walks through (a backtest you believe, chart-ingest parity, a prop account, then your own capital).
The prompt is the chassis. It is not an edge, and the ORB signal it drives is an example, not a
strategy to trade.

## How to use it

1. Open Claude Code in this repo (or your own, with your own signal study).
2. Paste the prompt below as one message. Say which signal study it should read.
3. Build it as **its own study** that reads the signal study's subgraph. Do not merge it into the
   signal file. The video's rule: one study finds the trade, one study manages the trade, never the
   same file. The signal-study convention in [`CLAUDE.md`](../../CLAUDE.md) still holds.
4. Deploy and compile the way [`sierra/DEPLOY.md`](../../sierra/DEPLOY.md) describes, on a **SIM**
   account, with the armed input OFF. Read the log. It should show what it *would* have done and
   send nothing.
5. Answer every question Claude asks about your account, instrument, and session before you arm
   anything.

## The prompt

```
I have a Sierra Chart ACSIL study that produces a LONG/SHORT signal. I want it to
place and manage the trade. Assume I am on a SIM account.

Requirements:
  1. An "armed" user input that defaults to OFF. With it off, the study logs what
     it WOULD have done and sends nothing. Nothing routes unless I set it on.
  2. On signal: send the entry with stop and target attached to the same order,
     not as follow-up orders.
  3. One position at a time. If a position is already open, the study does not
     re-enter, and it does not re-send on every tick while the condition holds.
  4. Position size is an input, not a constant.
  5. A separate always-available action that flattens the position and cancels
     all working orders, that does not depend on the strategy logic being correct.
  6. Handle and log: order rejected, no connection, position mismatch between what
     the study thinks it holds and what the account reports.
  7. Only evaluate the signal on a bar that has closed. With sc.AutoLoop the study
     re-runs on every tick of the forming bar, so without a bar-close gate it can
     write a signal on one tick and clear it on the next — the log fires, the chart
     ends up empty, and the two disagree with no error anywhere.

Tell me every place where your code assumes something about my account, my
instrument or my session that I have not told you. Do not invent an ACSIL function
signature — if you are unsure one exists, point me at the documentation page.
```

## Read it against the video

| Req | What it is in the video |
|---|---|
| 1 | The arming switch. Off is the default, and off still runs: you get the record without the risk. Written before any order code, on purpose. |
| 2 | Stop and target go out *with* the entry, not after the fill. The gap is small. It is not zero. |
| 3 | One position at a time, and the runaway re-entry bug: a condition that stays true re-fires every tick unless something says stop. |
| 4 | Size as an input, so it changes with the instrument or the regime without touching the signal. |
| 5 | The emergency flatten: the same "flatten all" button the platform has, available to the code when nobody is at the desk. |
| 6 | The mismatch the emergency stop watches for. The account is the record of truth. If the study can't tell what it holds, it gets flat. |
| 7 | The silent bug. The log records the yes, the chart records the no, and neither throws an error. |

## Versions

- **v1** (2026-09) — this file. Seven requirements.
- **v2** — built from the comments. The video ends by asking which safety requirement this prompt
  missed; the best answer goes into the next version, with credit.

Educational only. SIM by default. Not financial advice.
