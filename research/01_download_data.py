"""
STEP 1 — Build the BTC 5-minute candle file from the frozen Binance snapshot.

Reads binance_snapshot/ (official Binance monthly/daily ZIPs + SHA-256 checksums,
and one saved API response for the last partial day). Same files -> same numbers every run.
Any month/day that is not in the snapshot yet is downloaded once from Binance (needs internet)
and saved in binance_snapshot/, so later runs work offline with the same numbers.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import urllib.request
import zipfile
from datetime import datetime, timezone

import pandas as pd

from config import (DATA_CSV, DATA_META, END_UTC, INTERVAL, INTERVAL_MINUTES, SNAPSHOT_DIR,
                    START_UTC, SYMBOL, WARMUP_CANDLES)

ARCHIVE_URL = "https://data.binance.vision/data/spot/{kind}/klines/{sym}/{iv}/{name}"
BAR = pd.Timedelta(minutes=INTERVAL_MINUTES)
START = pd.Timestamp(START_UTC)
END = pd.Timestamp(END_UTC)
FIRST = START - BAR * WARMUP_CANDLES


def fetch(url: str, path) -> None:
    with urllib.request.urlopen(url, timeout=60) as r:
        path.write_bytes(r.read())
    print(f"  downloaded {path.name}")


def needed_files() -> list[tuple[str, str]]:
    """(kind, name): monthly ZIPs for full months, daily ZIPs for the last month."""
    files = []
    month = FIRST.normalize().replace(day=1)
    last_month = (END - BAR).normalize().replace(day=1)
    while month < last_month:
        files.append(("monthly", f"{SYMBOL}-{INTERVAL}-{month:%Y-%m}.zip"))
        month += pd.offsets.MonthBegin()
    day = last_month
    while day < (END - BAR).normalize():
        files.append(("daily", f"{SYMBOL}-{INTERVAL}-{day:%Y-%m-%d}.zip"))
        day += pd.Timedelta(days=1)
    return files


def read_zip(name: str, kind: str, download: bool) -> list[list]:
    path = SNAPSHOT_DIR / name
    check = SNAPSHOT_DIR / f"{name}.CHECKSUM"
    if not path.exists():
        # Not in the snapshot yet -> download it once from Binance and keep it in binance_snapshot/
        url = ARCHIVE_URL.format(kind=kind, sym=SYMBOL, iv=INTERVAL, name=name)
        try:
            fetch(url, path)
            fetch(url + ".CHECKSUM", check)
        except Exception as exc:
            path.unlink(missing_ok=True)
            raise RuntimeError(f"{name} is not in binance_snapshot/ and could not be downloaded "
                               f"from Binance ({exc}). Check the internet connection.") from exc
    if check.exists():
        expected = check.read_text(encoding="utf-8-sig").split()[0].lower()
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Checksum mismatch: {name}")
    with zipfile.ZipFile(path) as z:
        with z.open(z.namelist()[0]) as f:
            return [r for r in csv.reader(io.TextIOWrapper(f, encoding="utf-8")) if r and r[0].isdigit()]


def read_last_day(download: bool) -> list[list]:
    """The last (partial) day. Use a saved API response if there is one; otherwise try the
    official daily archive; if that is not published yet, ask the Binance API."""
    day = (END - BAR).normalize()
    api_path = SNAPSHOT_DIR / f"{SYMBOL}-{INTERVAL}-{day:%Y-%m-%d}-api.json"
    if api_path.exists():
        return json.loads(api_path.read_text())
    try:
        return read_zip(f"{SYMBOL}-{INTERVAL}-{day:%Y-%m-%d}.zip", "daily", download)
    except RuntimeError:
        pass
    start_ms = int(day.value // 1_000_000)
    end_ms = int(END.value // 1_000_000) - 1
    for host in ("data-api.binance.vision", "api.binance.com"):
        url = (f"https://{host}/api/v3/klines?symbol={SYMBOL}&interval={INTERVAL}"
               f"&startTime={start_ms}&endTime={end_ms}&limit=1000")
        try:
            fetch(url, api_path)
            return json.loads(api_path.read_text())
        except Exception as exc:
            print(f"  {host} failed: {exc}")
    return []


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true",
                        help="(kept for compatibility; missing files are always downloaded)")
    args = parser.parse_args()
    print("STEP 1: Building BTC candles (Binance files in binance_snapshot/, downloaded if missing)...")
    SNAPSHOT_DIR.mkdir(exist_ok=True)

    rows = []
    for kind, name in needed_files():
        rows += read_zip(name, kind, args.download)
    rows += read_last_day(args.download)

    df = pd.DataFrame([r[:8] for r in rows], columns=[
        "open_time", "Open", "High", "Low", "Close", "Volume", "close_time", "QuoteVolume"])
    t = df["open_time"].astype("int64")
    t = t.where(t < 10**14, t // 1000)          # Binance uses microseconds in new archives
    df["timestamp"] = pd.to_datetime(t, unit="ms", utc=True)
    for col in ["Open", "High", "Low", "Close", "Volume", "QuoteVolume"]:
        df[col] = df[col].astype(float)
    df = df[(df["timestamp"] >= FIRST) & (df["timestamp"] < END)]
    df = df.drop_duplicates("timestamp").sort_values("timestamp").reset_index(drop=True)

    expected = pd.date_range(FIRST, END, freq=BAR, inclusive="left")
    missing = expected.difference(pd.DatetimeIndex(df["timestamp"]))
    # Binance sometimes has short maintenance gaps. A few missing candles are OK (reported);
    # more than 0.5% means something is wrong with the files.
    if len(missing) > 0.005 * len(expected):
        raise ValueError(f"{len(missing)} candles missing, first: {list(missing[:3])}")
    if len(missing):
        print(f"  NOTE: {len(missing)} candles missing in Binance data (exchange gaps), e.g. {list(missing[:3])}")

    df["is_warmup"] = df["timestamp"] < START
    df = df[["timestamp", "Open", "High", "Low", "Close", "Volume", "QuoteVolume", "is_warmup"]]
    df.to_csv(DATA_CSV, index=False)

    meta = {
        "source": "Binance Spot snapshot (official archives + checksums)",
        "symbol": SYMBOL,
        "interval_minutes": INTERVAL_MINUTES,
        "study_start_utc": str(START),
        "study_end_utc_excluded": str(END),
        "study_start_pkt": f"{START.tz_convert('Asia/Karachi'):%Y-%m-%d %H:%M}",
        "study_end_pkt": f"{END.tz_convert('Asia/Karachi'):%Y-%m-%d %H:%M}",
        "study_months": int(round((END - START).days / 30.44)),
        "warmup_candles": WARMUP_CANDLES,
        "study_candles": int((~df["is_warmup"]).sum()),
        "rows": len(df),
        "missing_candles": int(len(missing)),
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    DATA_META.write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))
    print("STEP 1 DONE")


if __name__ == "__main__":
    main()
