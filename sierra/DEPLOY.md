# Sierra Chart — deploy, build, verify

How a `.cpp` in this repo becomes a study on a chart. Two commands and one menu path.

ACSIL — Sierra Chart's *Advanced Custom Study Interface and Language* — is C++ compiled
by Sierra Chart itself into a DLL it loads. There is no external toolchain to install and
no build step your agent can run: **the build is a GUI action**, so Claude Code writes and
deploys, and you press Build.

---

## The layout

```
<your clone>/
└── sierra/
    ├── DEPLOY.md          # this file
    ├── scripts/
    │   ├── deploy.ps1     # Windows / PowerShell
    │   └── deploy.sh      # Git Bash, WSL, macOS, Linux
    ├── studies/           # SOURCE OF TRUTH. One .cpp per study.
    ├── chartbooks/        # .Cht chartbooks
    └── exports/           # Export Chart Data CSVs land here

<your Sierra Chart install>/
└── ACS_Source/            # where Sierra Chart compiles from. Deploy TARGET.
    ├── sierrachart.h      # the API header
    ├── Studies.cpp ...    # ~38 stock example files. Reference material.
    └── OPTD_*.cpp         # your studies land here on deploy
```

**`sierra/studies/` is the source of truth. `ACS_Source` is a build output.** Edit in the
repo, deploy, build. Never edit a file inside `ACS_Source` — the next deploy silently
overwrites it and you lose the change with no error and no warning.

**Finding `ACS_Source`:** it sits directly inside your Sierra Chart installation folder,
next to `Data/`. It is the folder **Analysis → Build Custom Studies DLL** compiles from.

---

## Deploy

The scripts have **no default target** on purpose — Sierra Chart installs somewhere
different on every machine, and a script that guesses a path is a script that silently
deploys to the wrong install. Give it the path once:

```powershell
# Windows / PowerShell
$env:OPTD_SC_ACS_SOURCE = "<SierraChart>\ACS_Source"
powershell -ExecutionPolicy Bypass -File sierra\scripts\deploy.ps1
```

```bash
# Git Bash, WSL, macOS, Linux
export OPTD_SC_ACS_SOURCE="/path/to/SierraChart/ACS_Source"
bash sierra/scripts/deploy.sh
```

Or pass it per-run:

```powershell
powershell -ExecutionPolicy Bypass -File sierra\scripts\deploy.ps1 -Target "<SierraChart>\ACS_Source"
```

```bash
bash sierra/scripts/deploy.sh "/path/to/SierraChart/ACS_Source"
```

Either way it copies every `.cpp` and `.h` in `sierra/studies/` into `ACS_Source`, printing
each file and its size so you can see it actually moved. **Dry run first if you're unsure:**
add `-WhatIf` to the PowerShell version.

---

## Build

In Sierra Chart: **Analysis → Build Custom Studies DLL → Build →** the DLL named by
`SCDLLName()` in the source (here, `OPTD_Studies`).

The build output window is the thing to watch. Compiler errors carry line numbers that
refer to the file in `ACS_Source` — a byte-for-byte copy of your repo file, so the numbers
map straight back.

On success Sierra Chart writes the DLL into its `Data/` folder and reloads it in place. A
study already on a chart picks up new **code** immediately.

---

## Add it to a chart

**Analysis → Studies → Add Custom Study →** pick the DLL in the list → pick the study by
its `sc.GraphName` → **Add** → **Settings** to set inputs.

---

## Reference material — read it, don't recall it

`ACS_Source` also contains Sierra Chart's own example source: `sierrachart.h`,
`scconstants.h`, `scstructures.h`, `scdatetime.h`, `Template.cpp`, and `Studies.cpp`
through `Studies8.cpp`. It is authoritative, it ships with the platform, and it is the
best ACSIL documentation there is.

**ACSIL has a small public corpus, which is exactly the condition under which a model
invents a plausible function that does not exist.** So when working with an agent, add
`ACS_Source` as a readable directory and hold it to this rule:

> If you are not certain an ACSIL function exists with the signature you want, find it in
> `ACS_Source` and say which file and function you took it from. If you cannot find it
> there, say so and stop. Do not guess a signature.

Useful starting points:

| Looking for | Read |
|---|---|
| Minimal study skeleton | `Template.cpp` |
| High/low over a time-of-day window, held across the session, daily reset | `Studies6.cpp` → `scsf_HighLowForTimePeriodExtendedLines` |
| Session detection | `Studies.cpp` → `scsf_SessionIndicator` |
| Time-of-day comparison | `Studies8.cpp` → `scsf_TimeRangeHighlight` |
| Arrow subgraphs | `Studies2.cpp`, `Studies8.cpp` (`DRAWSTYLE_ARROW_UP` / `_DOWN`) |

---

## The four things that strand people

**1. "Studies" is greyed out.** No chart is in focus, or no symbol is loaded. Click the
chart first.

**2. `no custom study function names found ... internal function to file name map is empty`.**
The build produced a DLL with nothing exported. Almost always one of: the file isn't in
`ACS_Source` (deploy didn't run, or ran to a different install), `SCDLLName()` is missing,
or the study function isn't declared `SCSFExport`.

**3. `source file is missing`.** Sierra Chart is holding a stale path from a previous
build. Re-run the deploy, then re-open the build dialog so it re-scans the folder.

**4. You changed a default, a colour or a draw style and nothing happened.**
`sc.SetDefaults` only runs the first time a study is attached to a chart. Everything in
that block is already saved into the chartbook. **Remove the study and re-add it.** This
one costs people twenty minutes every time, and there is no error to tell you.

---

## Verify it before you believe it

A study that compiles is not a study that's right. Compiling means the syntax is legal.

1. **Chart.** Are the marks where the rule is true? Pick three by hand and walk to them.
2. **Export.** Right-click the chart → **Export Chart Data**. Open the CSV; the study's
   subgraph columns are in it. Levels non-zero across the session, signal columns non-zero
   only on signal bars.
3. **Do the chart and the export agree?** If the chart shows an arrow and the export shows
   zero on that bar, the study is evaluating the still-forming bar. That is the bar-close
   gate — `sc.GetBarHasClosedStatus() != BHCS_BAR_HAS_CLOSED` — and it is the single most
   common defect in a first ACSIL study.
4. **Recalculate twice.** Chart → **Recalculate** (Insert key), then again. If the second
   pass produces fewer signals than the first, persistent variables aren't being reset at
   `i == 0`. They live in the chartbook and are *restored* on reload, not zeroed.

---

## What's here

| File | What |
|---|---|
| `studies/OPTD_Opening_Range.cpp` | Opening Range Breakout **signal study**. Draws the OR high/low/mid, marks confirmed breakout bars, draws stop and target levels. |

**Signals only.** This study draws levels and marks bars. It does not place, modify or
manage any order and does not touch the trading API at all — so it stays verifiable on its
own, and nothing here can put on a position. The prompt that generated it is in
[`research/prompts/orb_sierra_chart_study.md`](../research/prompts/orb_sierra_chart_study.md);
regenerate it, or adapt it to a different rule.
