#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Download historical fire datasets: FRAP, GeoMAC, and WFIGS historical perimeters.

Usage:
    python historical_fires.py
    python historical_fires.py --start-date 2024-01-01 --end-date 2024-12-31
    python historical_fires.py --skip-frap
"""

import argparse
import json
import os
import shutil
import subprocess
import zipfile
from datetime import date, timedelta
from pathlib import Path

import requests

# ===== USER SETTINGS =====
START_DATE = os.environ.get("WFIGS_START_DATE", "2024-01-01")
END_DATE = os.environ.get("WFIGS_END_DATE", "2024-12-31")
ROOT = Path(os.environ.get("HISTORICAL_FIRES_OUTPUT_ROOT", "/home/runyang/ryang"))
FRAP_URL = "https://gis.data.cnra.ca.gov/api/download/v1/items/c3c10388e3b24cec8a954ba10458039d/shapefile?layers=0"
GEOMAC_URLS = {
    "Historic_Geomac_Perimeters_All_Years_2000_2018": "https://www.arcgis.com/sharing/rest/content/items/5b3ff19978be49208d41a9d9a461ecfb/data",
    "Historic_Geomac_Perimeters_2019": "https://www.arcgis.com/sharing/rest/content/items/48978dc5987e4fc19dce61ebdf02683b/data",
}
WFIGS_SERVICE = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Interagency_Perimeters/FeatureServer/0"
CHUNK_SIZE = 500


def range_dir_name(start_date: str, end_date: str) -> str:
    if start_date == "2024-01-01" and end_date == "2024-12-31":
        return "history_2024"
    return f"history_{start_date.replace('-', '_')}_to_{end_date.replace('-', '_')}"


def download_binary(session: requests.Session, url: str, out_file: Path, method="GET", data=None):
    if out_file.exists():
        print(f"[SKIP] {out_file}")
        return
    print(f"[GET ] {url}")
    if method == "POST":
        response = session.post(url, data=data, timeout=600, stream=True)
    else:
        response = session.get(url, timeout=600, stream=True)
    response.raise_for_status()
    out_file.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_file.with_suffix(out_file.suffix + ".part")
    with tmp.open("wb") as fh:
        for chunk in response.iter_content(1024 * 1024):
            if chunk:
                fh.write(chunk)
    tmp.replace(out_file)
    print(f"[OK  ] {out_file}")


def download_text(session: requests.Session, url: str, out_file: Path, method="GET", data=None):
    if out_file.exists():
        print(f"[SKIP] {out_file}")
        return out_file.read_text()
    print(f"[GET ] {url}")
    if method == "POST":
        response = session.post(url, data=data, timeout=600)
    else:
        response = session.get(url, timeout=600)
    response.raise_for_status()
    out_file.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_file.with_suffix(out_file.suffix + ".part")
    tmp.write_text(response.text)
    tmp.replace(out_file)
    print(f"[OK  ] {out_file}")
    return out_file.read_text()


def extract_zip(zip_path: Path, out_dir: Path):
    if out_dir.exists():
        print(f"[SKIP] {out_dir}")
        return
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(out_dir)
    print(f"[OK  ] extracted -> {out_dir}")


def chunked(items, size):
    for index in range(0, len(items), size):
        yield items[index:index + size]


def merge_parts_with_ogr2ogr(parts, gpkg: Path, layer_name: str):
    ogr2ogr = shutil.which("ogr2ogr")
    if ogr2ogr is None:
        print("[WARN] ogr2ogr not found, skip gpkg merge")
        return
    if gpkg.exists():
        print(f"[SKIP] {gpkg}")
        return
    first = True
    for part in parts:
        if first:
            subprocess.run([ogr2ogr, "-f", "GPKG", str(gpkg), str(part), "-nln", layer_name], check=True)
            first = False
        else:
            subprocess.run([ogr2ogr, "-f", "GPKG", "-update", "-append", str(gpkg), str(part), "-nln", layer_name], check=True)
    print(f"[OK  ] {gpkg}")


def download_frap(session: requests.Session):
    frap_dir = ROOT / "FRAP_Fire_Perimeters"
    zip_path = frap_dir / "California_Fire_Perimeters_All_shapefile.zip"
    download_binary(session, FRAP_URL, zip_path)
    extract_zip(zip_path, frap_dir / "shapefile")


def download_geomac(session: requests.Session):
    root = ROOT / "GeoMAC_Historical"
    for name, url in GEOMAC_URLS.items():
        data_dir = root / name
        zip_path = data_dir / f"{name}.zip"
        download_binary(session, url, zip_path)
        extract_zip(zip_path, data_dir / "extracted")


def download_wfigs(session: requests.Session, start_date: str, end_date: str):
    hist_dir = ROOT / "WFIGS_Perimeters" / range_dir_name(start_date, end_date)
    parts_dir = hist_dir / "parts"
    chunks_dir = hist_dir / "chunks"
    parts_dir.mkdir(parents=True, exist_ok=True)
    chunks_dir.mkdir(parents=True, exist_ok=True)

    if hist_dir.name == "history_2024":
        ids_json = hist_dir / "object_ids_2024.json"
        ids_txt = hist_dir / "object_ids_2024.txt"
        gpkg = hist_dir / "wfigs_interagency_perimeters_2024.gpkg"
        part_pattern = "wfigs_2024_part_{:04d}.geojson"
    else:
        ids_json = hist_dir / "object_ids.json"
        ids_txt = hist_dir / "object_ids.txt"
        gpkg = hist_dir / f"wfigs_interagency_perimeters_{hist_dir.name}.gpkg"
        part_pattern = "wfigs_part_{:04d}.geojson"

    metadata_file = hist_dir / "service_metadata.json"
    download_text(session, f"{WFIGS_SERVICE}?f=pjson", metadata_file)

    end_exclusive = date.fromisoformat(end_date) + timedelta(days=1)
    where = (
        f"poly_DateCurrent >= TIMESTAMP '{start_date} 00:00:00' AND "
        f"poly_DateCurrent < TIMESTAMP '{end_exclusive.isoformat()} 00:00:00'"
    )

    payload_text = download_text(
        session,
        f"{WFIGS_SERVICE}/query",
        ids_json,
        method="POST",
        data={"where": where, "returnIdsOnly": "true", "f": "json"},
    )
    object_ids = sorted(json.loads(payload_text).get("objectIds", []) or [])
    if not ids_txt.exists():
        ids_txt.write_text("\n".join(str(item) for item in object_ids) + ("\n" if object_ids else ""))
        print(f"[OK  ] {ids_txt}")
    else:
        print(f"[SKIP] {ids_txt}")

    part_files = []
    for index, id_chunk in enumerate(chunked(object_ids, CHUNK_SIZE), start=1):
        chunk_file = chunks_dir / f"ids_{index - 1:04d}"
        if not chunk_file.exists():
            chunk_file.write_text("\n".join(str(item) for item in id_chunk) + "\n")
            print(f"[OK  ] {chunk_file}")
        else:
            print(f"[SKIP] {chunk_file}")

        part_file = parts_dir / part_pattern.format(index)
        part_files.append(part_file)
        download_text(
            session,
            f"{WFIGS_SERVICE}/query",
            part_file,
            method="POST",
            data={
                "objectIds": ",".join(str(item) for item in id_chunk),
                "outFields": "*",
                "outSR": 4326,
                "f": "geojson",
            },
        )

    if part_files:
        merge_parts_with_ogr2ogr(part_files, gpkg, "wfigs_range")


def main():
    global ROOT
    parser = argparse.ArgumentParser(description="Download historical fire datasets.")
    parser.add_argument("--start-date", default=START_DATE, help="YYYY-MM-DD for WFIGS filter")
    parser.add_argument("--end-date", default=END_DATE, help="YYYY-MM-DD for WFIGS filter")
    parser.add_argument("--skip-frap", action="store_true", help="Skip FRAP")
    parser.add_argument("--skip-geomac", action="store_true", help="Skip GeoMAC")
    parser.add_argument("--skip-wfigs", action="store_true", help="Skip WFIGS historical")
    parser.add_argument("--output-root", default=str(ROOT), help="Root output directory")
    args = parser.parse_args()

    ROOT = Path(args.output_root)

    with requests.Session() as session:
        session.headers["User-Agent"] = "firemap-historical-fires/1.0"
        if not args.skip_frap:
            download_frap(session)
        if not args.skip_geomac:
            download_geomac(session)
        if not args.skip_wfigs:
            download_wfigs(session, args.start_date, args.end_date)

    print("All done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
