#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Download LANDFIRE existing vegetation type (EVT).

Usage:
    python vegetation_type.py
"""

import argparse
import os
import zipfile
from pathlib import Path

import requests

# ===== USER SETTINGS =====
VERSION = os.environ.get("LANDFIRE_EVT_VERSION", "LF2024")
OUTPUT_DIR = "/home/runyang/ryang/LANDFIRE_FUELS_2024/EVT"
URLS = {
    "LF2024": "https://landfire.gov/data-downloads/CONUS_LF2024/LF2024_EVT_CONUS.zip",
}


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
    folder_name = zip_path.stem
    target = out_dir / folder_name
    if target.exists():
        print(f"[SKIP] {target}")
        return
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(out_dir)
    print(f"[OK  ] extracted -> {out_dir}")


def main():
    parser = argparse.ArgumentParser(description="Download LANDFIRE EVT.")
    parser.add_argument("--version", default=VERSION, help="Dataset version key")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="Output directory")
    args = parser.parse_args()

    if args.version not in URLS:
        print(f"ERROR: unknown version {args.version}")
        return 1

    out_dir = Path(args.output_dir)
    zip_path = out_dir / Path(URLS[args.version]).name
    with requests.Session() as session:
        session.headers["User-Agent"] = "firemap-landfire-evt/1.0"
        download_file(session, URLS[args.version], zip_path)
    extract_zip(zip_path, out_dir)
    print("All done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
