"""Tick layer — a teaching Sierra Chart .scid reader, and where the intrabar truth lives.

The fills demo (`runs/run_fills_demo.py`) turns on one bit per bar: `up_first` — did
the high print before the low? That bit is the whole difference between honest fills
and fiction. But where does it come from? **Ticks.** A 1-minute OHLC bar has already
thrown it away; the raw tick sequence still has it.

This is the *teaching* version of a Sierra Chart `.scid` reader. A real `.scid` file is
a 56-byte header followed by fixed 40-byte records — a stream of ticks. Here we:

  1. generate a synthetic tick stream (random walk — zero real edge by construction),
  2. write it to a small binary file with the SAME shape as a `.scid` record,
  3. read it back by parsing the bytes (the actual skill), and
  4. aggregate ticks -> `Bar`s, deriving `up_first` from the real tick order.

Once you can read the ticks, you can reconstruct any strategy tick by tick — accurate
entries and exits — instead of trusting OHLC's guess about what happened inside a bar.

THE PRODUCTION HOOK: the production adapter reads *real* native `.scid` files (real
exchange ticks, timezone handling, and a parquet cache that replays years in seconds so
you can run thousands of permutations) through this same bars-from-ticks interface. That
adapter and the data stay private. The **format and the method are public** — that's this
file. Nothing here leaks an edge: the ticks are a random walk.

Real `.scid` record layout (Sierra Chart, little-endian) — we mirror a faithful subset:
    SCDateTime  int64   microseconds
    Open/High/Low/Close  4x float32   (for a pure tick, all four == the trade price)
    NumTrades / TotalVolume / BidVolume / AskVolume   4x uint32
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

import numpy as np

from data import Bar

# --- the on-disk format (faithful to .scid's header-then-fixed-records shape) ---
_MAGIC = b"SCID"
_HEADER_SIZE = 56
_RECORD_SIZE = 40
_HEADER = struct.pack("<4sIII40x", _MAGIC, _HEADER_SIZE, _RECORD_SIZE, 1)   # 56 bytes
_RECORD = struct.Struct("<q4f4I")                                            # 40 bytes

MINUTE_US = 60_000_000


@dataclass
class Tick:
    """One trade print: a microsecond timestamp, a price, a size. This is what a
    `.scid` record decodes to — and what an OHLC bar summarizes away."""

    t_us: int
    price: float
    volume: int


def synth_ticks(seed: int, n_minutes: int = 390, ticks_per_min: int = 20,
                start: float = 5000.0, tick_vol: float = 0.50) -> list[Tick]:
    """A deterministic synthetic tick stream — a pure random walk at tick resolution.

    Random walk is the point: no real edge exists in it, so any positive expectancy a
    backtest later reports is an artifact of the *fills*, not the strategy. Building the
    session tick-by-tick means the reconstructed bar's high, low, and `up_first` all come
    from a real (simulated) path — exactly as they would from real ticks.
    """
    rng = np.random.default_rng(seed)
    n = n_minutes * ticks_per_min
    prices = start + np.cumsum(rng.normal(0.0, tick_vol, size=n))
    vols = rng.integers(1, 5, size=n)
    dt_us = MINUTE_US // ticks_per_min
    return [Tick(t_us=i * dt_us, price=round(float(prices[i]), 2), volume=int(vols[i]))
            for i in range(n)]


def write_scid_like(path: str, ticks: list[Tick]) -> int:
    """Write ticks to a synthetic `.scid`-shaped binary file. Returns bytes written.

    For a pure tick, Sierra stores Open==High==Low==Close==price. We do the same, so the
    file you read back is byte-shaped like the real thing — you're learning the actual
    parse, just on data that can't leak an edge.
    """
    with open(path, "wb") as f:
        f.write(_HEADER)
        for tk in ticks:
            p = tk.price
            f.write(_RECORD.pack(tk.t_us, p, p, p, p, 1, tk.volume, 0, 0))
    return _HEADER_SIZE + len(ticks) * _RECORD_SIZE


def read_scid_like(path: str) -> list[Tick]:
    """Parse a `.scid`-shaped file back into ticks. This is the reader — the skill.

    Read the header, learn where records start and how big they are, then walk the file
    one fixed-size record at a time. A real `.scid` reader is this plus real timezone and
    epoch handling; the shape is identical.
    """
    with open(path, "rb") as f:
        header = f.read(_HEADER_SIZE)
        magic, header_size, record_size, _version = struct.unpack("<4sIII", header[:16])
        if magic != _MAGIC:
            raise ValueError(f"not a .scid-like file (magic={magic!r})")
        f.seek(header_size)                       # records begin after the header
        ticks: list[Tick] = []
        while (raw := f.read(record_size)) and len(raw) == record_size:
            t_us, _o, _h, _l, close, _ntr, total_vol, _bid, _ask = _RECORD.unpack(raw)
            ticks.append(Tick(t_us=t_us, price=close, volume=total_vol))
    return ticks


def bars_from_ticks(ticks: list[Tick], minute_us: int = MINUTE_US) -> list[Bar]:
    """Reconstruct 1-minute `Bar`s from a tick stream, deriving `up_first` from the ticks.

    This is the payoff. `open` is the first print of the minute, `close` the last, `high`/
    `low` the extremes — and `up_first` is *which extreme printed first*, read straight off
    the tick order. That last field is exactly what an OHLC feed cannot give you, and
    exactly what the honest-fills kernel needs. Same `Bar` the rest of the pipeline eats.
    """
    bars: list[Bar] = []
    bucket: int | None = None
    prices: list[float] = []

    def flush() -> None:
        hi, lo = max(prices), min(prices)
        bars.append(Bar(t=len(bars), open=prices[0], high=hi, low=lo,
                        close=prices[-1], up_first=prices.index(hi) < prices.index(lo)))

    for tk in ticks:
        b = tk.t_us // minute_us
        if bucket is None:
            bucket = b
        elif b != bucket:
            flush()
            prices = []
            bucket = b
        prices.append(tk.price)
    if prices:
        flush()
    return bars
