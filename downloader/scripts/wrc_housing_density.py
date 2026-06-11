#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Download and extract WRC 2018 housing density.

Usage:
    python wrc_housing_density.py
    python wrc_housing_density.py --url https://...
"""

import argparse
import os
import shutil
import subprocess
from pathlib import Path

import requests

# ===== USER SETTINGS =====
URL = os.environ.get("WRC_HOUSING_URL", "https://usfs-public.box.com/shared/static/g9v52r7m228jw3ue741hf9qa539vf738.zip")
OUTPUT_DIR = "./downloads/wrc_housing_density"
ZIP_NAME = "HUDen_CONUS.zip"


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
    unzip = shutil.which("unzip")
    if unzip is None:
        raise SystemExit("ERROR: unzip is required for this archive")
    out_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run([unzip, "-o", str(zip_path), "-d", str(out_dir)], check=True)
    print(f"[OK  ] extracted -> {out_dir}")


def main():
    parser = argparse.ArgumentParser(description="Download WRC housing density.")
    parser.add_argument("--url", default=URL, help="Download URL")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="Output directory")
    args = parser.parse_args()

    root = Path(args.output_dir)
    zip_path = root / ZIP_NAME
    with requests.Session() as session:
        session.headers["User-Agent"] = "firemap-wrc-housing/1.0"
        download_file(session, args.url, zip_path)
    extract_zip(zip_path, root / "extracted")
    print("All done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
