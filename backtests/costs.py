"""Costs — the cheats that come before a fill model is even involved.

`fills.py` covers one lie (same-bar sequencing). A backtest gets to cheat in two
more ways before any of that matters, and both are the *default* in most retail
tools:

  entry timing  — the strategy triggers on a bar's CLOSE, and the backtest enters
                  you at that close. You could not have known that price until the
                  bar was already over. Honest entry is the NEXT bar's open.

  costs         — zero commission, zero slippage. You trade for free, and you
                  always get your price.

Turn all three cheats on and you have the fantasy backtest. **Test one is to run
your strategy in that fantasy first.** If it loses money with every advantage a
backtest can fake, you are done — there was never anything there, and no amount of
honest modelling will rescue it.

The presets below mirror the cheat ladder: fantasy -> honest entry + commission ->
honest fills -> plus slippage. Change one thing at a time; when the numbers move,
you know exactly what moved them.

>>> Teaching layer. Commission here is a plausible retail futures rate. Slippage is
    the crossing cost on ES, which sits one tick wide the overwhelming majority of
    the session — but it is still a number from a chart, not from YOUR broker's
    fills. Edit both before you trust a dollar figure. The production desk measures
    slippage off the tick record instead of inheriting it. <<<
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Costs:
    """What a round turn actually costs you.

    `slippage_ticks` is per side — what you give up crossing the spread on a
    *market* order. Note that not every leg of a trade is a market order, which is
    why this class hands you `slip_points()` separately instead of only ever
    charging you twice; see `round_turn_dollars` for when each one applies.
    """

    commission_per_side: float = 0.0   # $ per contract per side
    slippage_ticks: float = 0.0        # ticks given up per side, market orders
    tick_size: float = 0.25            # ES
    point_value: float = 50.0          # $ per point, ES

    def slip_points(self) -> float:
        """Price given up crossing the spread, one side, in points.

        Apply this at the price level, not to the P&L, when a leg is a market
        order: pay up to get long, down to get short.
        """
        return self.slippage_ticks * self.tick_size

    def commission_round_turn(self) -> float:
        """Broker cost of getting in and back out of one contract."""
        return self.commission_per_side * 2

    def round_turn_dollars(self) -> float:
        """In and out with MARKET orders on both sides.

        Right for a plain hold — the drift control enters and exits at a close and
        crosses the spread both times. It is NOT right for a bracketed trade: the
        target is a resting *limit*, and a limit doesn't slip. It either fills at
        your price or never fills at all, which the honest fill model already
        accounts for. So a bracket pays entry slippage plus stop-exit slippage only
        — price those legs with `slip_points()` and charge commission separately.
        """
        return self.commission_round_turn() + self.slip_points() * self.point_value * 2


# The cheat ladder. One variable changes between each.
CHEAT = Costs()                                                   # P0  trade for free
COMMISSION_ONLY = Costs(commission_per_side=2.25)                 # P1  pay the broker
FULL = Costs(commission_per_side=2.25, slippage_ticks=0.53)       # P2b and cross the spread
