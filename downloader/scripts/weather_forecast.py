#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Download wildfire-relevant weather forecast layers from NDFD and HRRR.

Usage:
    python weather_forecast.py
    python weather_forecast.py --start-date 2024-07-01 --end-date 2024-07-07
    python weather_forecast.py --skip-hrrr
"""

import argparse
import os
import shutil
import subprocess
import time
from datetime import date, timedelta
from pathlib import Path

# ===== USER SETTINGS =====
START_DATE = os.environ.get("FORECAST_START_DATE", "2024-01-01")
END_DATE = os.environ.get("FORECAST_END_DATE", "2024-12-31")
NDFD_VARS = [
    item.strip()
    for item in os.environ.get(
        "NDFD_VARS",
        "critfireo,dryfireo,maxt,mint,maxrh,minrh,wspd,wdir,qpf",
    ).split(",")
    if item.strip()
]
HRRR_CYCLES = [
    item.strip()
    for item in os.environ.get("HRRR_CYCLES", "00,06,12,18").replace(" ", ",").split(",")
    if item.strip()
]
NDFD_DIR = "/home/runyang/ryang/NDFD"
HRRR_DIR = "/home/runyang/ryang/HRRR"
RETRY_MAX = int(os.environ.get("FORECAST_RETRY_MAX", "5"))
RETRY_DELAY = int(os.environ.get("FORECAST_RETRY_DELAY", "5"))


def iter_dates(start_str: str, end_str: str):
    start = date.fromisoformat(start_str)
    end = date.fromisoformat(end_str)
    if end < start:
        raise ValueError("END_DATE must be >= START_DATE")
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def run_command(command):
    for attempt in range(1, RETRY_MAX + 1):
        print("[RUN ]", " ".join(command))
        result = subprocess.run(command)
        if result.returncode == 0:
            return
        if attempt == RETRY_MAX:
            raise SystemExit(result.returncode)
        print(f"[RETRY] attempt {attempt}/{RETRY_MAX}")
        time.sleep(RETRY_DELAY)


def download_ndfd(start_date: str, end_date: str, output_dir: str, variables):
    root = Path(output_dir)
    for var in variables:
        for day in iter_dates(start_date, end_date):
            src = f"s3://noaa-ndfd-pds/wmo/{var}/{day:%Y}/{day:%m}/{day:%d}/"
            dst = root / var / f"{day:%Y}" / f"{day:%m}" / f"{day:%d}"
            dst.mkdir(parents=True, exist_ok=True)
            run_command([
                "aws", "s3", "sync", src, str(dst), "--no-sign-request", "--only-show-errors"
            ])


def download_hrrr(start_date: str, end_date: str, output_dir: str, cycles):
    root = Path(output_dir)
    for day in iter_dates(start_date, end_date):
        year_dir = root / f"{day:%Y}" / "wrfsfcf00"
        year_dir.mkdir(parents=True, exist_ok=True)
        day_tag = day.strftime("%Y%m%d")
        for cycle in cycles:
            base = f"hrrr.{day_tag}/conus/hrrr.t{cycle}z.wrfsfcf00.grib2"
            grib = year_dir / f"hrrr.{day_tag}.t{cycle}z.wrfsfcf00.grib2"
            idx = year_dir / f"hrrr.{day_tag}.t{cycle}z.wrfsfcf00.grib2.idx"
            if not grib.exists():
                run_command([
                    "aws", "s3", "cp",
                    f"s3://noaa-hrrr-bdp-pds/{base}",
                    str(grib),
                    "--no-sign-request",
                    "--only-show-errors",
                ])
            else:
                print(f"[SKIP] {grib}")
            if not idx.exists():
                run_command([
                    "aws", "s3", "cp",
                    f"s3://noaa-hrrr-bdp-pds/{base}.idx",
                    str(idx),
                    "--no-sign-request",
                    "--only-show-errors",
                ])
            else:
                print(f"[SKIP] {idx}")


def main():
    parser = argparse.ArgumentParser(description="Download NDFD + HRRR forecast data.")
    parser.add_argument("--start-date", default=START_DATE, help="YYYY-MM-DD")
    parser.add_argument("--end-date", default=END_DATE, help="YYYY-MM-DD")
    parser.add_argument("--ndfd-vars", default=",".join(NDFD_VARS), help="Comma-separated NDFD vars")
    parser.add_argument("--hrrr-cycles", default=",".join(HRRR_CYCLES), help="Comma-separated cycle hours")
    parser.add_argument("--skip-ndfd", action="store_true", help="Do not download NDFD")
    parser.add_argument("--skip-hrrr", action="store_true", help="Do not download HRRR")
    parser.add_argument("--ndfd-dir", default=NDFD_DIR, help="NDFD output directory")
    parser.add_argument("--hrrr-dir", default=HRRR_DIR, help="HRRR output directory")
    args = parser.parse_args()

    if shutil.which("aws") is None:
        print("ERROR: aws CLI is required")
        return 1

    variables = [item.strip() for item in args.ndfd_vars.split(",") if item.strip()]
    cycles = [item.strip() for item in args.hrrr_cycles.replace(" ", ",").split(",") if item.strip()]

    if not args.skip_ndfd:
        download_ndfd(args.start_date, args.end_date, args.ndfd_dir, variables)
    if not args.skip_hrrr:
        download_hrrr(args.start_date, args.end_date, args.hrrr_dir, cycles)

    print("All done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
