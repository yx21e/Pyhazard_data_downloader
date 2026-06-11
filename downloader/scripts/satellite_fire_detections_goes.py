#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Download GOES fire detection files (ABI-L2-FDCF) from NOAA open-data buckets.

Usage:
    python satellite_fire_detections_goes.py
    python satellite_fire_detections_goes.py --start-date 2024-08-01 --end-date 2024-08-03 --sats G16,G18
"""

import argparse
import os
import shutil
import subprocess
import time
from datetime import date, timedelta
from pathlib import Path

# ===== USER SETTINGS =====
START_DATE = os.environ.get("GOES_FDCF_START_DATE", "2024-01-01")
END_DATE = os.environ.get("GOES_FDCF_END_DATE", "2024-12-31")
SATS = os.environ.get("GOES_FDCF_SATS", "G16,G18")
PRODUCT = "ABI-L2-FDCF"
BUCKETS = {
    "G16": "noaa-goes16",
    "G18": "noaa-goes18",
}
OUTPUT_ROOT = Path(os.environ.get("GOES_FDCF_OUTPUT_ROOT", "./downloads/historical_fires"))
RETRY_MAX = int(os.environ.get("GOES_FDCF_RETRY_MAX", "5"))
RETRY_DELAY = int(os.environ.get("GOES_FDCF_RETRY_DELAY", "5"))


def iter_dates(start_str: str, end_str: str):
    start = date.fromisoformat(start_str)
    end = date.fromisoformat(end_str)
    if end < start:
        raise ValueError("END_DATE must be >= START_DATE")
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def sync_day(bucket: str, out_dir: Path, day: date):
    src = f"s3://{bucket}/{PRODUCT}/{day:%Y}/{day.timetuple().tm_yday:03d}/"
    dst = out_dir / f"{day:%Y}" / f"{day.timetuple().tm_yday:03d}"
    dst.mkdir(parents=True, exist_ok=True)
    command = ["aws", "s3", "sync", src, str(dst), "--no-sign-request", "--only-show-errors"]
    for attempt in range(1, RETRY_MAX + 1):
        print("[RUN ]", " ".join(command))
        result = subprocess.run(command)
        if result.returncode == 0:
            return
        if attempt == RETRY_MAX:
            raise SystemExit(result.returncode)
        print(f"[RETRY] {bucket} {day.isoformat()} attempt {attempt}/{RETRY_MAX}")
        time.sleep(RETRY_DELAY)


def main():
    parser = argparse.ArgumentParser(description="Download GOES FDCF files.")
    parser.add_argument("--start-date", default=START_DATE, help="YYYY-MM-DD")
    parser.add_argument("--end-date", default=END_DATE, help="YYYY-MM-DD")
    parser.add_argument("--sats", default=SATS, help="Comma-separated satellites: G16,G18")
    parser.add_argument("--output-root", default=str(OUTPUT_ROOT), help="Root output directory")
    args = parser.parse_args()

    if shutil.which("aws") is None:
        print("ERROR: aws CLI is required")
        return 1

    sats = [item.strip().upper() for item in args.sats.split(",") if item.strip()]
    output_root = Path(args.output_root)
    for sat in sats:
        bucket = BUCKETS[sat]
        out_dir = output_root / f"GOES_FDCF_{sat}"
        for day in iter_dates(args.start_date, args.end_date):
            sync_day(bucket, out_dir, day)

    print("All done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
