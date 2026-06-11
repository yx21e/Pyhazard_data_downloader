#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Download annual HMS smoke polygon bundle.

Usage:
    python smoke_analysis.py
    python smoke_analysis.py --year 2024
"""

import argparse
import os
import zipfile
from pathlib import Path

import requests

# ===== USER SETTINGS =====
YEAR = os.environ.get("HMS_YEAR", "2024")
OUTPUT_DIR = "./downloads/hms_smoke"
BASE_URL = "https://satepsanone.nesdis.noaa.gov/pub/FIRE/web/HMS/Smoke_Polygons/Shapefile/Annual_Bundles"


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


def extract_zip(zip_path: Path, out_dir: Path):
    if out_dir.exists() and any(out_dir.iterdir()):
        print(f"[SKIP] {out_dir}")
        return
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(out_dir)
    print(f"[OK  ] extracted -> {out_dir}")


def main():
    parser = argparse.ArgumentParser(description="Download annual HMS smoke polygons.")
    parser.add_argument("--year", default=YEAR, help="Bundle year")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="Output directory")
    args = parser.parse_args()

    year_root = Path(args.output_dir) / args.year
    zip_path = year_root / f"hms_smoke{args.year}.zip"
    shp_dir = year_root / "shapefile"
    url = f"{BASE_URL}/hms_smoke{args.year}.zip"

    with requests.Session() as session:
        session.headers["User-Agent"] = "firemap-hms-downloader/1.0"
        download_file(session, url, zip_path)
    extract_zip(zip_path, shp_dir)
    print("All done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
