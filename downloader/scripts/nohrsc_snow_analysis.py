#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Download daily NOHRSC SNODAS masked archives for a date range.

Usage:
    python nohrsc_snow_analysis.py
    python nohrsc_snow_analysis.py --start-date 2024-01-01 --end-date 2024-01-07
"""

import argparse
import os
from datetime import date, timedelta
from pathlib import Path

import requests

# ===== USER SETTINGS =====
START_DATE = os.environ.get("NOHRSC_START_DATE", "2024-01-01")
END_DATE = os.environ.get("NOHRSC_END_DATE", "2024-12-31")
OUTPUT_DIR = "./downloads/nohrsc_snow_analysis"
BASE_URL = "https://noaadata.apps.nsidc.org/NOAA/G02158/masked"


def iter_dates(start_str: str, end_str: str):
    start = date.fromisoformat(start_str)
    end = date.fromisoformat(end_str)
    if end < start:
        raise ValueError("END_DATE must be >= START_DATE")
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def month_dir(day: date) -> str:
    return day.strftime("%m_%b")


def download_file(session: requests.Session, url: str, out_file: Path):
    if out_file.exists():
        print(f"[SKIP] {out_file}")
        return

    print(f"[GET ] {url}")
    response = session.get(url, stream=True, timeout=600)
    if not response.ok:
        print(f"[FAIL] HTTP {response.status_code} -> {url}")
        return

    out_file.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_file.with_suffix(out_file.suffix + ".part")
    with tmp.open("wb") as fh:
        for chunk in response.iter_content(1024 * 1024):
            if chunk:
                fh.write(chunk)
    tmp.replace(out_file)
    print(f"[OK  ] {out_file}")


def main():
    parser = argparse.ArgumentParser(description="Download NOHRSC SNODAS masked archives.")
    parser.add_argument("--start-date", default=START_DATE, help="YYYY-MM-DD")
    parser.add_argument("--end-date", default=END_DATE, help="YYYY-MM-DD")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="Output directory")
    args = parser.parse_args()

    root = Path(args.output_dir)
    with requests.Session() as session:
        session.headers["User-Agent"] = "firemap-nohrsc-downloader/1.0"
        for day in iter_dates(args.start_date, args.end_date):
            name = f"SNODAS_{day:%Y%m%d}.tar"
            url = f"{BASE_URL}/{day:%Y}/{month_dir(day)}/{name}"
            download_file(session, url, root / month_dir(day) / name)

    print("All done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
