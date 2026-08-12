// The top of every ACSIL source file must include this line.
#include "sierrachart.h"

// Names the DLL that Sierra Chart builds from this workspace. Every study in this
// repo shares it, so they all land in one "OPTD_Studies" group in the study list.
SCDLLName("OPTD_Studies")

/*==============================================================================
  OPTD - Opening Range Breakout

  SIGNALS ONLY. This study draws levels and marks bars. It does not place,
  modify, cancel or manage any order, and it does not reference any order or
  position API at all. Nothing here executes.

  THE RULE (all times are time-of-day in the CHART's timezone; no conversion)

    1. A session runs from "Market Open Time" to "Session End Time" on each
       calendar date the chart contains.
    2. The opening range is built from the HIGHS and LOWS (never the closes) of
       every bar timestamped in [Market Open Time, Market Open Time + Opening
       Range Minutes).
    3. The range is COMPLETE at the first bar timestamped at or after
       Market Open Time + Opening Range Minutes. Before that moment nothing is
       drawn and no signal can fire.
    4. After completion and before Session End Time, count CONSECUTIVE closed
       bars whose close is strictly above OR High. When the count reaches
       "Confirmation Closes", a LONG signal fires on that bar.
    5. Mirrored for SHORT: consecutive closes strictly below OR Low.
    6. A close back inside the range zeros both counters. A close beyond one
       rail zeros the opposite counter.
    7. At most one long and one short per session. A side that has fired is
       done for the day; the other side can still fire.
    8. Nothing fires outside the session, inside the opening-range window, at
       or after Session End Time, or on a bar that has not closed.
    9. NO RANGE, NO SIGNALS. A session that never completes an opening-range
       window - half day, holiday, data gap, chart starting mid-session -
       produces no levels and no signals. There is no partial-range fallback,
       and yesterday's range is never carried into today.
   10. On a signal bar, Stop and Target are computed from that bar's close and
       held for the rest of the session. They are DRAWN LEVELS ONLY. Nothing
       tracks whether they are reached.

  THE BAR-CLOSE GATE (the single most important line in this file)

    sc.GetBarHasClosedStatus() != BHCS_BAR_HAS_CLOSED -> return.

    Without it the study re-evaluates the still-forming bar on every incoming
    tick. A condition can be true on one tick and false two ticks later, so the
    message log shows a signal that the chart never draws and the export shows
    as zero: three places that should agree and none of them do. The gate does
    NOT suppress history - sierrachart.h (GetBarHasClosedStatus, around line
    104) flags only the single element at ArraySize-1 as not-closed, so every
    historical bar, including all of them during a full recalculation, passes.

  A NOTE ON BAR TIMESTAMPS

    Sierra Chart timestamps an intraday bar at the START of its period unless
    the chart has "Use Bar Ending Date-Time" enabled. This study reads the bar
    timestamp and nothing else, consistently: a bar is in the range window if
    its timestamp is in [open, open+minutes), and the range completes on the
    first bar whose timestamp is at or after open+minutes. Under the default
    start-timestamping that completion bar is the first bar entirely past the
    window, which means every bar that contributed to the range has fully
    closed - no lookahead, no half-formed bar in the range. With bar-ending
    timestamps enabled everything shifts by one bar.

  SetDefaults RUNS ONCE

    Sierra Chart only runs the sc.SetDefaults block the first time the study is
    added to a chart. If you edit a default value, a color or a draw style
    below, an already-attached instance will NOT pick it up on rebuild. Remove
    the study from the chart and re-add it.
==============================================================================*/

// Keys for sc.GetPersistentInt / sc.GetPersistentDouble. These are just slot
// numbers; the values live in the chartbook. Named so the reads below are
// readable, and in an anonymous namespace so they cannot collide with another
// study's file in the same DLL.
namespace
{
	// Per-session integer state.
	const int KEY_SESSION_DATE   = 1;  // calendar date of the session being processed
	const int KEY_SESSION_VALID  = 2;  // 1 if we saw this session from its start
	const int KEY_RANGE_STATE    = 3;  // 0 forming, 1 complete, -1 failed for this session
	const int KEY_OR_BAR_COUNT   = 4;  // bars that landed inside the range window
	const int KEY_LONG_COUNT     = 5;  // consecutive closes above OR High
	const int KEY_SHORT_COUNT    = 6;  // consecutive closes below OR Low
	const int KEY_LONG_FIRED     = 7;  // long already fired this session
	const int KEY_SHORT_FIRED    = 8;  // short already fired this session
	const int KEY_RISK_LINES     = 9;  // 0 none, 1 stop only, 2 stop and target

	// Per-session price state.
	const int KEY_OR_HIGH        = 1;
	const int KEY_OR_LOW         = 2;
	const int KEY_STOP           = 3;
	const int KEY_TARGET         = 4;

	// Range states for KEY_RANGE_STATE.
	const int RANGE_FORMING  =  0;
	const int RANGE_COMPLETE =  1;
	const int RANGE_FAILED   = -1;
}

/*============================================================================*/
SCSFExport scsf_OPTD_OpeningRange(SCStudyInterfaceRef sc)
{
	// Subgraphs are the study's output arrays. One value per bar. Using
	// subgraphs rather than drawing tools is deliberate: they reset naturally
	// each day, survive a recalculation, and show up in Export Chart Data,
	// which is how the study gets verified.
	SCSubgraphRef Subgraph_ORHigh      = sc.Subgraph[0];
	SCSubgraphRef Subgraph_ORLow       = sc.Subgraph[1];
	SCSubgraphRef Subgraph_ORMid       = sc.Subgraph[2];
	SCSubgraphRef Subgraph_LongSignal  = sc.Subgraph[3];
	SCSubgraphRef Subgraph_ShortSignal = sc.Subgraph[4];
	SCSubgraphRef Subgraph_Stop        = sc.Subgraph[5];
	SCSubgraphRef Subgraph_Target      = sc.Subgraph[6];

	// Every threshold, time and count the rule mentions is a user input.
	// There are no magic numbers in the logic below.
	SCInputRef Input_MarketOpenTime   = sc.Input[0];
	SCInputRef Input_ORMinutes        = sc.Input[1];
	SCInputRef Input_SessionEndTime   = sc.Input[2];
	SCInputRef Input_ConfirmCloses    = sc.Input[3];
	SCInputRef Input_RiskPoints       = sc.Input[4];
	SCInputRef Input_UseORWidthAsRisk = sc.Input[5];
	SCInputRef Input_TargetRMultiple  = sc.Input[6];
	SCInputRef Input_ShowORLines      = sc.Input[7];
	SCInputRef Input_ShowMidline      = sc.Input[8];
	SCInputRef Input_ShowStopTarget   = sc.Input[9];
	SCInputRef Input_ShowArrows       = sc.Input[10];
	SCInputRef Input_LogSignals       = sc.Input[11];

	//--------------------------------------------------------------------------
	// Section 1 - defaults. Runs once, when the study is first added.
	// Do NOT read an input's value in here: SetDefaults runs before the user's
	// saved settings are applied, so a read returns an unset value.
	//--------------------------------------------------------------------------
	if (sc.SetDefaults)
	{
		sc.GraphName = "OPTD - Opening Range Breakout";
		sc.StudyDescription =
			"Opening range breakout signal study. Draws the opening range high, low and "
			"midline, marks confirmed breakout bars, and draws stop and target levels. "
			"Signals only - this study does not place or manage orders.";

		sc.GraphRegion = 0;   // 0 is the main price panel
		sc.AutoLoop = 1;      // Sierra calls this function once per bar, sc.Index is the bar
		sc.ValueFormat = VALUEFORMAT_INHERITED;  // price levels format like the chart's prices

		// Level subgraphs. STAIR_STEP holds a flat line across the bars that
		// carry a value. DrawZeros = false is what makes zero mean "nothing
		// here" - without it every day's line would be dragged down to zero
		// and joined to the next day.
		Subgraph_ORHigh.Name = "OR High";
		Subgraph_ORHigh.DrawStyle = DRAWSTYLE_STAIR_STEP;
		Subgraph_ORHigh.PrimaryColor = RGB(0, 200, 255);
		Subgraph_ORHigh.LineWidth = 2;
		Subgraph_ORHigh.DrawZeros = false;

		Subgraph_ORLow.Name = "OR Low";
		Subgraph_ORLow.DrawStyle = DRAWSTYLE_STAIR_STEP;
		Subgraph_ORLow.PrimaryColor = RGB(0, 200, 255);
		Subgraph_ORLow.LineWidth = 2;
		Subgraph_ORLow.DrawZeros = false;

		Subgraph_ORMid.Name = "OR Mid";
		Subgraph_ORMid.DrawStyle = DRAWSTYLE_STAIR_STEP;
		Subgraph_ORMid.PrimaryColor = RGB(128, 128, 128);
		Subgraph_ORMid.LineWidth = 1;
		Subgraph_ORMid.DrawZeros = false;

		// Signal subgraphs. Non-zero on the signal bar only.
		Subgraph_LongSignal.Name = "Long Signal";
		Subgraph_LongSignal.DrawStyle = DRAWSTYLE_ARROW_UP;
		Subgraph_LongSignal.PrimaryColor = RGB(0, 255, 0);
		Subgraph_LongSignal.LineWidth = 2;   // arrow size
		Subgraph_LongSignal.DrawZeros = false;

		Subgraph_ShortSignal.Name = "Short Signal";
		Subgraph_ShortSignal.DrawStyle = DRAWSTYLE_ARROW_DOWN;
		Subgraph_ShortSignal.PrimaryColor = RGB(255, 0, 0);
		Subgraph_ShortSignal.LineWidth = 2;
		Subgraph_ShortSignal.DrawZeros = false;

		Subgraph_Stop.Name = "Stop";
		Subgraph_Stop.DrawStyle = DRAWSTYLE_STAIR_STEP;
		Subgraph_Stop.PrimaryColor = RGB(255, 80, 80);
		Subgraph_Stop.LineWidth = 1;
		Subgraph_Stop.DrawZeros = false;

		Subgraph_Target.Name = "Target";
		Subgraph_Target.DrawStyle = DRAWSTYLE_STAIR_STEP;
		Subgraph_Target.PrimaryColor = RGB(80, 255, 80);
		Subgraph_Target.LineWidth = 1;
		Subgraph_Target.DrawZeros = false;

		// SetTime takes seconds since midnight. HMS_TIME is deprecated in
		// scdatetime.h, so build the value with SCDateTime instead.
		Input_MarketOpenTime.Name = "Market Open Time";
		Input_MarketOpenTime.SetTime(SCDateTime(9, 30, 0, 0).GetTime());

		Input_ORMinutes.Name = "Opening Range Minutes";
		Input_ORMinutes.SetInt(30);
		Input_ORMinutes.SetIntLimits(1, 600);

		Input_SessionEndTime.Name = "Session End Time";
		Input_SessionEndTime.SetTime(SCDateTime(16, 0, 0, 0).GetTime());

		Input_ConfirmCloses.Name = "Confirmation Closes";
		Input_ConfirmCloses.SetInt(1);
		Input_ConfirmCloses.SetIntLimits(1, 50);

		Input_RiskPoints.Name = "Risk Points";
		Input_RiskPoints.SetFloat(20.0f);
		Input_RiskPoints.SetFloatLimits(0.0f, static_cast<float>(MAX_STUDY_LENGTH));

		Input_UseORWidthAsRisk.Name = "Use OR Width As Risk";
		Input_UseORWidthAsRisk.SetYesNo(false);

		Input_TargetRMultiple.Name = "Target R Multiple";
		Input_TargetRMultiple.SetFloat(2.0f);
		Input_TargetRMultiple.SetFloatLimits(0.0f, static_cast<float>(MAX_STUDY_LENGTH));

		Input_ShowORLines.Name = "Show Opening Range Lines";
		Input_ShowORLines.SetYesNo(true);

		Input_ShowMidline.Name = "Show Midline";
		Input_ShowMidline.SetYesNo(true);

		Input_ShowStopTarget.Name = "Show Stop/Target Lines";
		Input_ShowStopTarget.SetYesNo(true);

		Input_ShowArrows.Name = "Show Signal Arrows";
		Input_ShowArrows.SetYesNo(true);

		Input_LogSignals.Name = "Log Signals To Message Log";
		Input_LogSignals.SetYesNo(false);

		return;
	}

	//--------------------------------------------------------------------------
	// Section 2 - read the inputs. This is the runtime body, so the values here
	// are the user's actual settings.
	//--------------------------------------------------------------------------

	// Input.GetTime() returns seconds since midnight as a plain int, and
	// SCDateTime::GetTimeInSeconds() returns the same thing for a bar. That is
	// the comparison scsf_TimeRangeHighlight in Studies8.cpp uses, and it is why
	// no timezone conversion happens anywhere in this file.
	const int MarketOpenSeconds = Input_MarketOpenTime.GetTime();
	const int SessionEndSeconds = Input_SessionEndTime.GetTime();
	const int ORWindowEndSeconds = MarketOpenSeconds + Input_ORMinutes.GetInt() * 60;

	const int ConfirmationCloses = Input_ConfirmCloses.GetInt();
	const double RiskPoints      = Input_RiskPoints.GetFloat();
	const bool UseORWidthAsRisk  = Input_UseORWidthAsRisk.GetYesNo() != 0;
	const double TargetRMultiple = Input_TargetRMultiple.GetFloat();

	const bool ShowORLines    = Input_ShowORLines.GetYesNo() != 0;
	const bool ShowMidline    = Input_ShowMidline.GetYesNo() != 0;
	const bool ShowStopTarget = Input_ShowStopTarget.GetYesNo() != 0;
	const bool ShowArrows     = Input_ShowArrows.GetYesNo() != 0;
	const bool LogSignals     = Input_LogSignals.GetYesNo() != 0;

	//--------------------------------------------------------------------------
	// Section 3 - THE BAR-CLOSE GATE. See the header comment. This must come
	// before any state is touched, not just before the signal test, or a
	// forming bar would still be able to advance a counter.
	//--------------------------------------------------------------------------
	if (sc.GetBarHasClosedStatus() != BHCS_BAR_HAS_CLOSED)
		return;

	const int i = sc.Index;

	//--------------------------------------------------------------------------
	// Section 4 - persistent state.
	//
	// These live in the chartbook and are RESTORED on reload, not zeroed. If
	// they are not explicitly cleared at the start of a recalculation the study
	// works the first time and emits nothing ever after, because the "already
	// fired" flags are still set from the previous run.
	//--------------------------------------------------------------------------
	int& r_SessionDate  = sc.GetPersistentInt(KEY_SESSION_DATE);
	int& r_SessionValid = sc.GetPersistentInt(KEY_SESSION_VALID);
	int& r_RangeState   = sc.GetPersistentInt(KEY_RANGE_STATE);
	int& r_ORBarCount   = sc.GetPersistentInt(KEY_OR_BAR_COUNT);
	int& r_LongCount    = sc.GetPersistentInt(KEY_LONG_COUNT);
	int& r_ShortCount   = sc.GetPersistentInt(KEY_SHORT_COUNT);
	int& r_LongFired    = sc.GetPersistentInt(KEY_LONG_FIRED);
	int& r_ShortFired   = sc.GetPersistentInt(KEY_SHORT_FIRED);
	int& r_RiskLines    = sc.GetPersistentInt(KEY_RISK_LINES);

	double& r_ORHigh = sc.GetPersistentDouble(KEY_OR_HIGH);
	double& r_ORLow  = sc.GetPersistentDouble(KEY_OR_LOW);
	double& r_Stop   = sc.GetPersistentDouble(KEY_STOP);
	double& r_Target = sc.GetPersistentDouble(KEY_TARGET);

	if (i == 0)
	{
		// Clear every single one. A value left behind here is the classic
		// "works once, then never again" bug.
		r_SessionDate  = 0;   // 0 is "no session seen yet", so bar 0 below
		r_SessionValid = 0;   // takes the new-session branch like any other
		r_RangeState   = RANGE_FORMING;   // first bar of a date
		r_ORBarCount   = 0;
		r_LongCount    = 0;
		r_ShortCount   = 0;
		r_LongFired    = 0;
		r_ShortFired   = 0;
		r_RiskLines    = 0;
		r_ORHigh = 0.0;
		r_ORLow  = 0.0;
		r_Stop   = 0.0;
		r_Target = 0.0;

		// Deliberately no return here. Bar 0 is a real bar and on a chart
		// loaded with day-session data only it IS the 09:30 bar - the first
		// bar of the opening range and the evidence that we saw the session
		// start. Returning would silently throw both away and kill day one.
		// The reset above is the part that matters; falling through costs
		// nothing because the reset left the state exactly as if this were
		// the first bar of a fresh session.
	}

	const int BarDate = sc.BaseDateTimeIn[i].GetDate();
	const int BarTime = sc.BaseDateTimeIn[i].GetTimeInSeconds();

	//--------------------------------------------------------------------------
	// Section 5 - session rollover, detected from the bar timestamps.
	//
	// Nothing here assumes bar 0 is a session start, and nothing assumes a bar
	// lands exactly on Market Open Time. A change of calendar date is the only
	// trigger.
	//--------------------------------------------------------------------------
	if (BarDate != r_SessionDate)
	{
		r_SessionDate = BarDate;
		r_RangeState  = RANGE_FORMING;
		r_ORBarCount  = 0;
		r_LongCount   = 0;
		r_ShortCount  = 0;
		r_LongFired   = 0;
		r_ShortFired  = 0;
		r_RiskLines   = 0;
		r_ORHigh = 0.0;
		r_ORLow  = 0.0;
		r_Stop   = 0.0;
		r_Target = 0.0;

		// Rule 9, the "chart starts mid-session" half of it. A range built
		// from 09:45 onward is indistinguishable from a real one once it is
		// built, so the check has to happen here, at the first bar of the
		// date: did we actually see this day from before the open?
		//
		// A 24-hour chart's first bar of the date is around midnight, so this
		// passes. A day-session chart's first bar is exactly the open, which
		// also passes. A chart whose data begins at 09:45 does not, and that
		// session then produces no levels and no signals.
		r_SessionValid = (BarTime <= MarketOpenSeconds) ? 1 : 0;
	}

	// A session we never saw the start of is dead for the whole day. No
	// partial-range fallback, and nothing from the previous day survives,
	// because the block above already cleared it.
	if (!r_SessionValid)
		return;

	//--------------------------------------------------------------------------
	// Section 6 - build the opening range.
	//
	// HIGHS and LOWS, never closes. Window is [open, open+minutes), half-open
	// so the bar timestamped exactly at the end belongs to the post-range
	// period and not to both.
	//--------------------------------------------------------------------------
	if (r_RangeState == RANGE_FORMING
		&& BarTime >= MarketOpenSeconds
		&& BarTime < ORWindowEndSeconds)
	{
		const double BarHigh = sc.High[i];
		const double BarLow  = sc.Low[i];

		if (r_ORBarCount == 0)
		{
			r_ORHigh = BarHigh;
			r_ORLow  = BarLow;
		}
		else
		{
			if (BarHigh > r_ORHigh)
				r_ORHigh = BarHigh;
			if (BarLow < r_ORLow)
				r_ORLow = BarLow;
		}

		++r_ORBarCount;
	}

	//--------------------------------------------------------------------------
	// Section 7 - complete the range.
	//
	// The first bar at or after the window end freezes it. Under Sierra's
	// default bar-start timestamps every bar that fed the range has closed by
	// now, so this bar is itself eligible to signal - no lookahead is involved.
	//--------------------------------------------------------------------------
	if (r_RangeState == RANGE_FORMING && BarTime >= ORWindowEndSeconds)
	{
		// The other half of rule 9: a session whose window contained no bars
		// at all - holiday, data gap, or a chart that ends before the window
		// closes and therefore never reaches this branch anyway - fails for
		// good rather than falling back to a partial range.
		if (r_ORBarCount > 0)
		{
			r_RangeState = RANGE_COMPLETE;
		}
		else
		{
			r_RangeState = RANGE_FAILED;
			r_ORHigh = 0.0;
			r_ORLow  = 0.0;
		}
	}

	if (r_RangeState != RANGE_COMPLETE)
		return;

	//--------------------------------------------------------------------------
	// Section 8 - the active part of the session: range complete, session not
	// over. Outside this window the subgraphs are left at zero, which combined
	// with DrawZeros = false is what keeps one day's lines from joining the
	// next day's. It is also what makes the overnight bars on a 24-hour chart
	// draw nothing.
	//--------------------------------------------------------------------------
	if (BarTime < ORWindowEndSeconds || BarTime >= SessionEndSeconds)
		return;

	// Levels carry their value on EVERY bar in this window, not just the first,
	// so the line is continuous and the export has a value on every row.
	if (ShowORLines)
	{
		Subgraph_ORHigh[i] = static_cast<t_ChartArrayDataType>(r_ORHigh);
		Subgraph_ORLow[i]  = static_cast<t_ChartArrayDataType>(r_ORLow);
	}

	if (ShowMidline)
		Subgraph_ORMid[i] = static_cast<t_ChartArrayDataType>((r_ORHigh + r_ORLow) * 0.5);

	//--------------------------------------------------------------------------
	// Section 9 - the breakout counters.
	//
	// Strictly above / strictly below, so a close exactly on a rail counts as
	// inside the range and resets both counters. Only bar i is ever read; no
	// value from a later bar is involved in any decision here.
	//--------------------------------------------------------------------------
	const double BarClose = sc.Close[i];

	if (BarClose > r_ORHigh)
	{
		++r_LongCount;
		r_ShortCount = 0;      // a close beyond one rail zeros the opposite side
	}
	else if (BarClose < r_ORLow)
	{
		++r_ShortCount;
		r_LongCount = 0;
	}
	else
	{
		// Back inside the range: both sides start over.
		r_LongCount  = 0;
		r_ShortCount = 0;
	}

	//--------------------------------------------------------------------------
	// Section 10 - fire at most one signal per side per session, and hold the
	// risk levels that go with it.
	//
	// Risk levels are drawn and nothing else. There is no notion of the trade
	// being filled, stopped or closed, because nothing is traded.
	//--------------------------------------------------------------------------
	int FiredDirection = 0;   // +1 long, -1 short, 0 nothing this bar

	if (!r_LongFired && r_LongCount >= ConfirmationCloses)
	{
		r_LongFired = 1;
		FiredDirection = 1;

		if (ShowArrows)
			Subgraph_LongSignal[i] = sc.Low[i];   // arrow sits under the bar
	}
	else if (!r_ShortFired && r_ShortCount >= ConfirmationCloses)
	{
		r_ShortFired = 1;
		FiredDirection = -1;

		if (ShowArrows)
			Subgraph_ShortSignal[i] = sc.High[i]; // arrow sits over the bar
	}

	if (FiredDirection != 0)
	{
		const double Risk = UseORWidthAsRisk ? (r_ORHigh - r_ORLow) : RiskPoints;

		if (FiredDirection > 0)
		{
			r_Stop   = BarClose - Risk;
			r_Target = BarClose + Risk * TargetRMultiple;
		}
		else
		{
			r_Stop   = BarClose + Risk;
			r_Target = BarClose - Risk * TargetRMultiple;
		}

		// Target R Multiple of 0 means no target line at all, so record that
		// only the stop is live. If both sides fire in one session the second
		// signal's levels replace the first's - there is one Stop subgraph and
		// one Target subgraph, so the most recent signal owns them.
		r_RiskLines = (TargetRMultiple > 0.0) ? 2 : 1;

		if (LogSignals)
		{
			// ASCII only - this string goes to the Sierra Chart message log.
			SCString Message;
			Message.Format(
				"OPTD Opening Range: %s signal  %s  Close %s  OR High %s  OR Low %s  Stop %s  Target %s",
				(FiredDirection > 0) ? "LONG" : "SHORT",
				sc.FormatDateTime(sc.BaseDateTimeIn[i]).GetChars(),
				sc.FormatGraphValue(BarClose, sc.BaseGraphValueFormat).GetChars(),
				sc.FormatGraphValue(r_ORHigh, sc.BaseGraphValueFormat).GetChars(),
				sc.FormatGraphValue(r_ORLow,  sc.BaseGraphValueFormat).GetChars(),
				sc.FormatGraphValue(r_Stop,   sc.BaseGraphValueFormat).GetChars(),
				(r_RiskLines == 2)
					? sc.FormatGraphValue(r_Target, sc.BaseGraphValueFormat).GetChars()
					: "none");

			sc.AddMessageToLog(Message, 0);
		}
	}

	//--------------------------------------------------------------------------
	// Section 11 - hold the risk levels across the rest of the session,
	// starting on the signal bar itself.
	//--------------------------------------------------------------------------
	if (ShowStopTarget && r_RiskLines > 0)
	{
		Subgraph_Stop[i] = static_cast<t_ChartArrayDataType>(r_Stop);

		if (r_RiskLines == 2)
			Subgraph_Target[i] = static_cast<t_ChartArrayDataType>(r_Target);
	}
}
