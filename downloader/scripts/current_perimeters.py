#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Download current WFIGS interagency fire perimeters.

Usage:
    python current_perimeters.py
"""

import argparse
import os
from pathlib import Path

import requests

# ===== USER SETTINGS =====
OUTPUT_DIR = "/home/runyang/ryang/WFIGS_Perimeters/current"
SERVICE_ROOT = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Interagency_Perimeters_Current/FeatureServer/0"


def download_text(session: requests.Session, url: str, out_file: Path, method="GET", data=None):
    if out_file.exists():
        print(f"[SKIP] {out_file}")
        return
    print(f"[GET ] {url}")
    if method == "POST":
        response = session.post(url, data=data, timeout=300)
    else:
        response = session.get(url, timeout=300)
    response.raise_for_status()
    out_file.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_file.with_suffix(out_file.suffix + ".part")
    tmp.write_text(response.text)
    tmp.replace(out_file)
    print(f"[OK  ] {out_file}")


def main():
    parser = argparse.ArgumentParser(description="Download current WFIGS perimeters.")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="Output directory")
    args = parser.parse_args()

    root = Path(args.output_dir)
    with requests.Session() as session:
        session.headers["User-Agent"] = "firemap-current-perimeters/1.0"
        download_text(session, f"{SERVICE_ROOT}?f=pjson", root / "service_metadata.json")
        download_text(
            session,
            f"{SERVICE_ROOT}/query",
            root / "wfigs_current.geojson",
            method="POST",
            data={
                "where": "1=1",
                "outFields": "*",
                "outSR": 4326,
                "f": "geojson",
            },
        )

    print("All done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
