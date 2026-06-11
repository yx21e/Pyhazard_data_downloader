#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Download NASA GIBS daily imagery layers plus capability documents.

Usage:
    python nasa_gibs.py
    python nasa_gibs.py --start-date 2024-06-01 --end-date 2024-06-03 --layers MODIS_Terra_CorrectedReflectance_TrueColor
"""

import argparse
import os
from datetime import date, timedelta
from pathlib import Path

import requests

# ===== USER SETTINGS =====
START_DATE = os.environ.get("GIBS_START_DATE", "2024-01-01")
END_DATE = os.environ.get("GIBS_END_DATE", "2024-12-31")
LAYERS = os.environ.get(
    "GIBS_LAYERS",
    "MODIS_Terra_CorrectedReflectance_TrueColor,VIIRS_SNPP_CorrectedReflectance_TrueColor",
)
OUTPUT_DIR = "./downloads/nasa_gibs"
WMS_CAPS = "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?request=GetCapabilities&service=WMS"
WMTS_CAPS = "https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/1.0.0/WMTSCapabilities.xml"


def iter_dates(start_str: str, end_str: str):
    start = date.fromisoformat(start_str)
    end = date.fromisoformat(end_str)
    if end < start:
        raise ValueError("END_DATE must be >= START_DATE")
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def build_wms_url(layer: str, day: date) -> str:
    return (
        "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi"
        "?service=WMS"
        "&request=GetMap"
        "&version=1.3.0"
        f"&layers={layer}"
        "&styles="
        "&format=image/jpeg"
        "&transparent=false"
        "&height=1024"
        "&width=2048"
        "&crs=EPSG:4326"
        "&bbox=-90,-180,90,180"
        f"&time={day.isoformat()}"
    )


def download_file(session: requests.Session, url: str, out_file: Path):
    if out_file.exists():
        print(f"[SKIP] {out_file}")
        return
    print(f"[GET ] {url}")
    response = session.get(url, stream=True, timeout=180)
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
    parser = argparse.ArgumentParser(description="Download NASA GIBS imagery.")
    parser.add_argument("--start-date", default=START_DATE, help="YYYY-MM-DD")
    parser.add_argument("--end-date", default=END_DATE, help="YYYY-MM-DD")
    parser.add_argument("--layers", default=LAYERS, help="Comma-separated GIBS layer names")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="Output directory")
    args = parser.parse_args()

    root = Path(args.output_dir)
    layers = [item.strip() for item in args.layers.split(",") if item.strip()]
    with requests.Session() as session:
        session.headers["User-Agent"] = "firemap-gibs-downloader/1.0"
        download_file(session, WMS_CAPS, root / "capabilities" / "WMS_GetCapabilities.xml")
        download_file(session, WMTS_CAPS, root / "capabilities" / "WMTS_GetCapabilities.xml")
        for layer in layers:
            for day in iter_dates(args.start_date, args.end_date):
                download_file(session, build_wms_url(layer, day), root / layer / f"{day.isoformat()}.jpg")

    print("All done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
