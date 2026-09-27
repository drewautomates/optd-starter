# Bias check — one-shot prompt

Paste this into Claude Code from inside **your own** backtest folder. If you've cloned this repo,
you can instead run the skill from here: `/bias-check <path-to-your-folder>` (the full method lives
in [`.claude/skills/bias-check/SKILL.md`](../../.claude/skills/bias-check/SKILL.md)).

It checks for lookahead first, then reviews every indicator, then the rest of the pipeline, and it
runs things instead of only reading them. It doesn't edit your code.

---

```text
Audit this backtest for bias. Treat the result it reports as a claim to disprove, not a result to
explain. Do not edit any of my files: put every harness, probe and re-run in a new folder
_bias_check/ and write the final report to _bias_check/REPORT.md. Run Python with -B so nothing
lands in my folder. Before changing anything, reproduce my headline number exactly (trade count and
net) from your harness; if my backtest is one script, port its loop into a function first. Ask me
once, up front, how many variants I tried before this one; don't wait for the answer.

1. MAP THE PIPELINE. Before judging anything, show me how the number is made, with file:line for
   each stage: data load (resolution, timezone of the index, session filter), bar building (is a
   bar's timestamp its open or its close? how are higher-timeframe bars made?), every indicator and
   its timeframe, the signal and the bar it's evaluated on, entry price and bar, exits (and how a bar
   that touches both stop and target is resolved), costs, accounting (equity frequency for drawdown,
   denominator for per-month), and how many variants were tried before this one.

2. LOOKAHEAD. For every signal and indicator:
   - Entry at the signal bar or the next bar? Show me the line. Re-run with next-bar-open entry and
     put both results side by side.
   - When a lower-timeframe signal reads a higher-timeframe input, which bar does it read at the
     first minute and the last minute of the period: the forming one or the last completed one?
     Prove it with timestamps.
   - Is any feature constant all session? When was its value actually known?
   - What timezone is the index in? Print the first and last bar my session filter keeps on one
     day, and how many bars it keeps.
   - Does the simulated price path start at the entry time or at the start of the signal bar?

3. PROBE IT. For each indicator and signal function, write a harness that computes it on the full
   data, then again with every bar after i deleted, for every bar i in one session. If the value
   at i ever changes, it read the future: list where. Then compute it from two different history
   start dates (use offsets that are not multiples of the higher timeframe, e.g. 0, 7 and 53 bars)
   and diff the last 100 bars; if they differ after warm-up, it depends on how much history was
   loaded, or the higher-timeframe bars are built by counting rows instead of reading the clock.
   Check one or two sessions, not the whole file.

4. THE REST OF THE PIPELINE.
   - Fills: when stop and target are both inside one bar, which fills? For every stop exit, was the
     fill inside the range that actually traded?
   - Costs: what share of gross goes to commission and slippage? What does one tick worse per fill do?
   - Drift: would holding over the same bars with no signal have made the same money?
   - Accounting: is drawdown on daily or trade-level equity? Is per-month divided by calendar months?
   - Selection: how many variants were tried? Was any parameter chosen on the data it's reported on?
   - Benchmark: does it beat buy-and-hold on the same instrument, at matched risk, after costs?

5. REPORT. Start with one headline line: the number, what it becomes with the biggest single fix,
   and the fully honest number with every fix stacked. Then findings, most severe first. RED = a
   re-run shows the number moves. AMBER = the code allows it but no run has shown it. GREY = it ran
   and didn't move because this data never triggered it (give the count). BLUE = a missing
   safeguard. For each: file:line, the mechanism in one sentence, the evidence with both numbers
   side by side, and the smallest fix as a suggestion.
   List every check you couldn't run and what it needs. Change one variable per re-run, and if a
   fix makes the result look worse than it should, report that too.
```
