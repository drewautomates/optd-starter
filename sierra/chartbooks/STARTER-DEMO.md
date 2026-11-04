# OPTD starter demo chartbook

**From the video:** How to set up Sierra Chart ([`i8tH-DIdgLg`](https://youtu.be/i8tH-DIdgLg)). It's the finished chart the video opens on.

**What you get:** one Sierra Chart chartbook, [`OPTD-starter-demo.Cht`](OPTD-starter-demo.Cht) ([direct download](https://github.com/drewautomates/optd-starter/raw/main/sierra/chartbooks/OPTD-starter-demo.Cht)):

- **MES, 1-minute candles**
- **VWAP with its bands** (Sierra's built-in *Volume Weighted Average Price* study)
- **Large trade bubbles** (Sierra's built-in *Large Volume Trade Indicator*)

It uses built-in studies only, so there's nothing to compile, no custom DLL and no ACSIL. It holds no credentials and no account settings.

**What it isn't:** a strategy. On their own, these two studies aren't an edge. They give context: where active traders are, where the larger buyers and sellers show up, and whether price is holding above or below VWAP for the day.

## Load it (2 minutes)

1. Download this repo (or just the `.Cht` file above).
2. Open your Sierra Chart install folder, then its **`Data`** folder. That's where your chartbooks and symbol data live.
3. Drag `OPTD-starter-demo.Cht` into `Data`.
4. In Sierra Chart: **File → Open Chartbook** → pick **OPTD-starter-demo**.
5. **It opened blank?** Your data/trade service is different from mine. Go to **Edit → Translate Symbols to Current Service**, and the MES chart fills in from your feed.

Check two things before you trust the chart:

- **Time zone:** Global Settings → Time Zone. Set it to the zone you actually trade in. Borrowed chartbooks are where this goes wrong.
- **Contract:** the chart is on a specific MES contract. After a roll, either select the new contract or switch the chart to a continuous contract (Chart Settings → Symbol), as shown in the video.

## Versions

- 2026-11-04 · first version, shipped with the Sierra Chart setup video.
