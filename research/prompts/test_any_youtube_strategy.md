# Test any YouTube trading strategy honestly: the starter prompt (v1)

Ships with video 14, [I Reverse Engineered TJR's Strategy With AI and Tested It on 7 Years of Data](https://youtu.be/o4fuU_pa0bw).
One prompt for plain Claude Code. It takes a strategy video's transcript and walks it through the same steps the
video does: pull the rules out, freeze every gap as a named assumption, prove the code finds the setups the video
shows, then run seven tests in order and grade it "survived to X".

**What it gets you:** a written rule sheet with a quote for every rule, a numbered list of every assumption you
had to make (decided before any result exists), a backtest where each assumption is a parameter, the 7-test table
with a grade, and a coin-flip comparison that separates the entry from the exits.

**What it does not get you:** data, or an edge. You bring your own bars, and most strategies won't survive. The
point is that you find out honestly. It also doesn't judge the person who made the video. It tests the rules as
stated and as you coded them, and it says so.

## How to use it

1. Get the transcript of the strategy video. Any transcript works (YouTube's own, or a tool that pulls it).
2. Make an empty folder and put your bars in `./data/` (1-minute bars are what the video uses). Know the
   instrument, the bar size and the timezone the timestamps are in.
3. Open Claude Code in that folder and paste the prompt below. Fill the four blanks and paste the transcript where
   it says so.
4. Go one step at a time. It stops after each step for your OK. **Read the assumptions list (step 2) before you
   say OK**: that's where a test quietly becomes your strategy instead of theirs.
5. Don't type "rules frozen" until you're done changing anything. The holdout runs once.

## The prompt

```
I want to test a trading strategy from a YouTube video, honestly, the way a professional would.
Work in this folder. Go one step at a time and STOP after each step for my OK.

MY SETUP (ask me if anything is blank, never assume):
  Data: ____ (instrument, bar size, where the files are, what timezone they're in)
  Research period: ____   Holdout period: ____   (split the holdout off now; don't load it until I say "rules frozen")
  Costs: commission $____ per contract per side + ____ tick(s) slippage on every market order
  Size: 1 contract

THE TRANSCRIPT:
  <paste it here>

STEP 0 · DEFINE IT. What style of trading is this? Define every term he uses: plain English, his word, the
  standard name, and the exact definition you'd code.
STEP 1 · KNOWNS. List every rule he STATES, each with the exact quote. Separate his performance claims (the bar
  we test against). List everything a backtest needs that he never says.
STEP 2 · ASSUMPTIONS. For every gap: a numbered assumption (A1, A2, ...) with the most LITERAL reading of his
  words, a reason, and 1-2 neighbour values to test later. No results exist yet, so don't pick what looks good.
STEP 3 · TEST PLAN. Write down, before any run: the split, costs, and what passes each test:
  1 TIME       recompute 50 random signals on data cut off at the signal bar; any change = lookahead = fail
  2 MATCH      run it on the exact days he shows in the video; print every step; does it take his trades?
  3 FIT        honest version (next-bar fill, costs, targets need 1 tick through) next to a cheat version;
               the honest one must be positive
  4 FILL       still positive with 2 ticks slippage; if a bar hits stop and target, assume the stop
  5 FLUKE      1,000 coin-flip runs: same days, same stop distance, same exits, random direction + minute;
               must beat the 95th percentile
  6 COUNT      flip every assumption to its neighbours; all must agree in sign; log every run in trials.csv
  7 BENCHMARK  beat buy-and-hold at the same daily volatility
  plus a GATE ABLATION: remove each filter one at a time. If removing one doesn't hurt, it isn't the edge.
STEP 4 · BUILD. Every assumption is a named parameter. Higher timeframes only from completed bars. Before the
  first run, list every place you assumed something about my data I didn't tell you.
STEP 5 · BASELINE. Run the 7 tests on the research period. Grade = "survived to X" (the last test passed in
  order). Report win rate per trade, per trade excluding break-evens, and per day, against his claim.
STEP 6 · TRY TO FIX IT, HONESTLY. Before running anything, list the permutations and a selection rule. Run them on
  the first half of the research period, take the survivors to the second half ONCE, print the trial count next
  to every number.
STEP 7 · HOLDOUT. Only after I type "rules frozen": run the holdout once and refuse a second run.

Never tune to make it look better. If a result is bad, report it as it is.
Output: results.md (assumptions, the 7-test table, the grade), trades.csv, equity.png, coinflip.png.
```

## Read it against the video

| Piece of the prompt | Why it's there | Where the video shows it |
|---|---|---|
| A quote for every rule (step 1) | Stops you testing your own version of the strategy | The setup in plain words (0:46) |
| Assumptions before results (step 2) | Stops you picking the reading that wins. The video ended with 21 | The assumptions (1:23), two rules with two jobs: either index sweeps, both agree (2:13), freeze it (2:26) |
| MATCH on the video's own days (test 2) | Proves the code sees what he sees. Without it, a bad result is just "you coded it wrong". The first run took zero trades; four fixes on his own days got it to his days and his direction every time. It still entered earlier than he did on every day we could check, and making it enter like him four ways didn't change the result | 3:13, 4:03 and 7:46 |
| Coin flip with the same stops (test 5) | Separates the entry from the exits. If random entries do as well, the setup isn't the edge | 5:00 and 5:59 |
| Gate ablation | Finds the one rule doing the work, and the filters that only look like they help | 6:28 |
| Trial count + holdout once (steps 6–7) | Run enough tests and something looks good by luck. 54 tests in the video; the "fix" that went 4 for 4 lost on years it hadn't seen | 7:06 and 10:11 |
| Three win rates (step 5) | A break-even counts as a win, so win rate climbs without anyone lying. It isn't edge; per-trade result after costs is | 8:09 and 9:17 |

## Versions

- **v1** (video 14): the 8-step prompt the video's test was built from, condensed to one page. Seven tests in
  order (TIME · MATCH · FIT · FILL · FLUKE · COUNT · BENCHMARK), graded "survived to X".
