#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Download GOES MCMIPC files that can be rendered into GeoColor imagery.

Usage:
    python goes_geocolor.py
    python goes_geocolor.py --start-date 2024-08-01 --end-date 2024-08-03 --sats G16,G18 --hour 18
"""

import argparse
import os
import re
from datetime import date, timedelta
from pathlib import Path

import requests

# ===== USER SETTINGS =====
START_DATE = os.environ.get("GOES_START_DATE", "2024-01-01")
END_DATE = os.environ.get("GOES_END_DATE", "2024-12-31")
HOUR = os.environ.get("GOES_HOUR", "18")
SATS = os.environ.get("GOES_SATS", "G16,G18")
OUTPUT_DIR = "/home/runyang/ryang/GOES_MCMIPC_2024"
PRODUCT = "ABI-L2-MCMIPC"
BUCKETS = {
    "G16": "noaa-goes16",
    "G18": "noaa-goes18",
}


def iter_dates(start_str: str, end_str: str):
    start = date.fromisoformat(start_str)
    end = date.fromisoformat(end_str)
    if end < start:
        raise ValueError("END_DATE must be >= START_DATE")
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def julian_day(day: date) -> str:
    return f"{day.timetuple().tm_yday:03d}"


def list_first_key(session: requests.Session, bucket: str, day: date, hour: str):
    prefix = f"{PRODUCT}/{day.year}/{julian_day(day)}/{hour}/"
    url = f"https://{bucket}.s3.amazonaws.com/?prefix={prefix}"
    response = session.get(url, timeout=120)
    response.raise_for_status()
    match = re.search(r"<Key>([^<]+)</Key>", response.text)
    return match.group(1) if match else None


def download_file(session: requests.Session, url: str, out_file: Path):
    if out_file.exists():
        print(f"[SKIP] {out_file}")
        return
    print(f"[GET ] {url}")
    response = session.get(url, stream=True, timeout=600)
    response.raise_for_status()
    out_file.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_file.with_suffix(out_file.suffix + ".part")
    with tmp.open("wb") as fh:
        for chunk in response.iter_content(1024 * 1024):
            if chunk:
                fh.write(chunk)
    tmp.replace(out_file)
    print(f"[OK  ] {out_file}")


def main():
    parser = argparse.ArgumentParser(description="Download GOES MCMIPC GeoColor source files.")
    parser.add_argument("--start-date", default=START_DATE, help="YYYY-MM-DD")
    parser.add_argument("--end-date", default=END_DATE, help="YYYY-MM-DD")
    parser.add_argument("--hour", default=HOUR, help="UTC hour, e.g. 18")
    parser.add_argument("--sats", default=SATS, help="Comma-separated satellites: G16,G18")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="Output directory")
    args = parser.parse_args()

    root = Path(args.output_dir)
    sats = [item.strip().upper() for item in args.sats.split(",") if item.strip()]

    with requests.Session() as session:
        session.headers["User-Agent"] = "firemap-goes-geocolor/1.0"
        for sat in sats:
            bucket = BUCKETS[sat]
            for day in iter_dates(args.start_date, args.end_date):
                key = list_first_key(session, bucket, day, args.hour)
                if not key:
                    print(f"[MISS] {sat} {day.isoformat()} no file under hour {args.hour}")
                    continue
                out_file = root / sat / f"{day.year}" / julian_day(day) / Path(key).name
                download_file(session, f"https://{bucket}.s3.amazonaws.com/{key}", out_file)

    print("All done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
