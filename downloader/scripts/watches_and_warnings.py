#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Download NDFD watches and warnings bulletin files (wwa) for a date range.

Usage:
    python watches_and_warnings.py
    python watches_and_warnings.py --start-date 2024-01-01 --end-date 2024-01-31
"""

import argparse
import os
import shutil
import subprocess
import time
from datetime import date, timedelta
from pathlib import Path

# ===== USER SETTINGS =====
START_DATE = os.environ.get("NDFD_START_DATE", "2024-01-01")
END_DATE = os.environ.get("NDFD_END_DATE", "2024-12-31")
OUTPUT_DIR = "./downloads/ndfd"
RETRY_MAX = int(os.environ.get("NDFD_RETRY_MAX", "5"))
RETRY_DELAY = int(os.environ.get("NDFD_RETRY_DELAY", "5"))
VARIABLE = "wwa"


def iter_dates(start_str: str, end_str: str):
    start = date.fromisoformat(start_str)
    end = date.fromisoformat(end_str)
    if end < start:
        raise ValueError("END_DATE must be >= START_DATE")
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def run_sync(src: str, dst: Path):
    dst.mkdir(parents=True, exist_ok=True)
    command = [
        "aws",
        "s3",
        "sync",
        src,
        str(dst),
        "--no-sign-request",
        "--only-show-errors",
    ]
    for attempt in range(1, RETRY_MAX + 1):
        print("[RUN ]", " ".join(command))
        result = subprocess.run(command)
        if result.returncode == 0:
            return
        if attempt == RETRY_MAX:
            raise SystemExit(result.returncode)
        print(f"[RETRY] {src} attempt {attempt}/{RETRY_MAX}")
        time.sleep(RETRY_DELAY)


def main():
    parser = argparse.ArgumentParser(description="Download NDFD watches and warnings (wwa).")
    parser.add_argument("--start-date", default=START_DATE, help="YYYY-MM-DD")
    parser.add_argument("--end-date", default=END_DATE, help="YYYY-MM-DD")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="Root NDFD output directory")
    args = parser.parse_args()

    if shutil.which("aws") is None:
        print("ERROR: aws CLI is required")
        return 1

    root = Path(args.output_dir)
    for day in iter_dates(args.start_date, args.end_date):
        src = f"s3://noaa-ndfd-pds/wmo/{VARIABLE}/{day:%Y}/{day:%m}/{day:%d}/"
        dst = root / VARIABLE / f"{day:%Y}" / f"{day:%m}" / f"{day:%d}"
        run_sync(src, dst)

    print("All done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
