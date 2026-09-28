# Backtest pipeline — the starter prompt (v1)

Ships with video 10, **How to Backtest a Strategy in Sierra Chart (Without Fooling Yourself)**.
This is the prompt shown on screen in that video, verbatim.

**What it gets you:** a Python backtester that reads Sierra Chart's own tick files, stitches the
futures contracts together at the roll, and runs your strategy with honest entries, fills and costs.
It prints a day-by-day trade calendar and every trade's MFE and MAE, how far it went for you and
against you. Then it checks itself with the [bias check](../../.claude/skills/bias-check/SKILL.md).

**What it does not get you:** an edge. The pipeline is the part that stops you fooling yourself. What
you run through it is yours. The ORB in this repo is an example, not a strategy to trade.

## Before you paste it

- **Get the data.** In Sierra Chart, open a chart of each contract you want to test (for example
  `NQZ25`, `NQH26`) and let the historical tick data download. Sierra writes one tick file per
  contract into its `Data` folder (`NQZ25-CME.scid` and so on; the exact name depends on your data
  service). The Base package's historical data service covers CME tick data back to 2011.
- **No Sierra yet?** Add one line to the prompt: *"I don't have data yet. First generate two or
  three synthetic quarterly contracts in the real .scid layout, with a price gap at each roll, a
  daylight-saving switch and some overnight ticks, and build against those."* The code shouldn't change
  when you point it at real files. (This repo's `data/tick/demo.scid` is a teaching file for the reader
  in video 3. Its timestamps are minute counters, not real dates, so don't use it for this.)
- **Use it with Claude Code** in your own folder. Paste the prompt as one message and fill in the
  blanks at the top. For the last step, open Claude Code inside this repo and run
  `/bias-check <your folder>`.

## The prompt

```
Build me a Python backtester that reads Sierra Chart .scid tick files directly.

My setup (ask me for anything I leave blank; don't assume):
  - Instrument and contracts: ____   (e.g. NQ, quarterly H/M/U/Z, $20/point, 0.25 tick;
    or a stock, e.g. SPY)
  - Session and timezone I trade: ____   (e.g. 9:30-16:00 US/Eastern, flat by the close,
    last entry by 15:00)
  - Strategy rules: ____   (signal timeframe, signal, where R is measured from, stop,
    target, one position at a time)
  - Costs: ____   (commission per contract per side, slippage in ticks per fill)
  - Holdout: the most recent year, or the last 20% if I have under three years.
    Split it off before the first run.

Requirements:
  1. Read the .scid files directly: 56-byte header, then 40-byte records, timestamps in
     microseconds since 1899-12-30 UTC. Confirm the layout against Sierra Chart's
     documentation. For a tick record, Close is the trade price, Open is 0 (or a marker
     value), and High/Low are the ask and bid. If the records are bars instead of ticks,
     stop and tell me.
  2. Timezone first. The file is UTC. Convert to my session's timezone before any session
     filter. Once the bars exist, print the first and last bar kept on one sample day and
     how many bars a normal session has, so I can see it's right. Weekends and holidays
     out. Early-close days: drop them or flatten at the early close, and say which.
  3. Build 1-minute bars from the ticks. A bar is stamped at its CLOSE. For every bar,
     keep whether the high or the low printed first. Higher timeframes are built from
     clock time, not by counting rows.
  4. Contract rolls. Each contract is its own file. The old contract trades through the
     second Friday of its expiry month; the new one takes over the Monday after. Make the
     roll date a setting, and check it against my Sierra continuous chart. Stitch the
     contracts into one series. If an indicator needs a continuous price history,
     back-adjust the earlier contract by the gap between the two, measured at the last
     minute both traded on the roll Friday. Fills always come from the real contract's
     own ticks. No trade is held across a roll. If it's a stock, there is no roll: adjust
     the price history for splits and dividends instead, and skip the rest of this step.
  5. Signals only use data that existed when the bar closed. Any higher-timeframe input
     reads the last COMPLETED bar, never the one still forming.
  6. Enter at the next bar's open, not the close of the signal bar.
  7. Exits walk the ticks after entry, in order. If the data can't say whether the stop
     or the target printed first (bar records, not ticks), assume the stop.
  8. Stops and targets sit on the tick grid. Targets are limit orders: tell me whether
     you fill them on a touch or only when price trades through. Commission and slippage
     on every fill. Show results with and without costs, side by side.
  9. Output: a day-by-day calendar of every trade (contract, win/loss, R, $), and each
     trade's MFE and MAE in R. Drawdown on trade-by-trade equity. Per-month figures
     divided by calendar months, not days with a trade.
 10. Keep a trial log. Every run gets a line with its parameters, whether I keep it or
     not, so I always know how many versions I've tried. Print the count next to every
     result.
 11. The holdout stays untouched until I say the rules are frozen. Then run it once, and
     refuse a second run.
 12. Compare against doing nothing: buy-and-hold on the same instrument, sized to the
     same daily dollar volatility, after costs.

When it runs, I'll audit it with /bias-check from the optd-starter repo. Fix what it
finds, log every audit re-run as a trial, and never run an audit on the holdout. Tell
me every place your code assumes something about my data, instrument or session that
I haven't told you.
```

## Read it against the video

| Req | What it is in the video |
|---|---|
| 1 | Sierra's tick files on your machine are the advantage: standardised, local, and cheap. Reading them is the first step, so it's done from the documented format, not from a guess. |
| 2 | The first thing that lied to me: a UTC file and a Pacific session. Hours of chasing prices that didn't match. |
| 3 | Bars stamped at the close, and the intrabar truth kept, so the fills can be honest later. Clock-built higher timeframes, because counting rows drifts when the file starts at a different minute. |
| 4 | The futures question nobody answers: roll in the week before expiry, stitch, back-adjust only for indicators, fill on the real contract. On a stock, splits and dividends take the roll's place. |
| 5 | The one that cost a week: the ten-minute candle that knew its own close. |
| 6 | The entry you could actually have had. |
| 7 | Bar data can't tell whether the stop or the target hit first. Ticks can. |
| 8 | Costs are the boring part that kills thin edges. |
| 9 | The calendar and MFE/MAE: the data I wanted and couldn't get from the replay. |
| 10 | Tuning isn't overfitting. Forgetting how many versions you tried is. The count is what the deflated Sharpe in the video is judged against. |
| 11 | One untouched holdout, split off before the first run. Once you peek and retune, it isn't holdout data any more. |
| 12 | Would doing nothing have beaten it? |

## Versions

- **v1** (2026-09): this file. Twelve requirements. This is the starter version: the full pipeline
  (trial statistics with the deflated Sharpe, and a random-entry benchmark) isn't public yet. If you'd
  use it, say so on the download page. Tested end to end against synthetic quarterly
  contracts across a roll and a daylight-saving switch before release.

Educational only. Backtests aren't live results. Not financial advice.
