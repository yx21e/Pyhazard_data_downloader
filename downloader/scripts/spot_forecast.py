#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Download current/recent Spot Forecast products from api.weather.gov.

Usage:
    python spot_forecast.py
    python spot_forecast.py --locations EKA,SGX --max-products 20
"""

import argparse
import json
import os
from pathlib import Path

import requests

# ===== USER SETTINGS =====
LOCATIONS = os.environ.get("SPOT_LOCATIONS", "")
MAX_PRODUCTS = int(os.environ.get("SPOT_MAX_PRODUCTS", "0"))
OUTPUT_DIR = "/home/runyang/ryang/Spot_Forecast_Current"
BASE_URL = "https://api.weather.gov"


def parse_locations(raw: str):
    return [item.strip().upper() for item in raw.replace(",", " ").split() if item.strip()]


def download_json(session: requests.Session, url: str, out_file: Path):
    if out_file.exists():
        print(f"[SKIP] {out_file}")
        return json.loads(out_file.read_text())

    print(f"[GET ] {url}")
    response = session.get(url, timeout=180)
    response.raise_for_status()
    payload = response.json()
    out_file.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_file.with_suffix(out_file.suffix + ".part")
    tmp.write_text(json.dumps(payload, indent=2))
    tmp.replace(out_file)
    print(f"[OK  ] {out_file}")
    return payload


def main():
    parser = argparse.ArgumentParser(description="Download current/recent Spot Forecast products.")
    parser.add_argument("--locations", default=LOCATIONS, help="Comma- or space-separated office ids")
    parser.add_argument("--max-products", type=int, default=MAX_PRODUCTS, help="Max products per office, 0 means all returned")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="Output directory")
    args = parser.parse_args()

    root = Path(args.output_dir)
    root.mkdir(parents=True, exist_ok=True)
    (root / "access_scope.txt").write_text(
        "Source: NOAA NWS api.weather.gov\n"
        "This endpoint provides current/recent Spot Forecast product listings and product text.\n"
        "It is not a guaranteed full historical archive.\n"
    )

    with requests.Session() as session:
        session.headers.update({
            "User-Agent": "firemap-spot-forecast/1.0",
            "Accept": "application/geo+json, application/json",
        })

        locations_index = download_json(session, f"{BASE_URL}/products/types/FWS/locations", root / "locations.json")
        entries = locations_index.get("locations", {})
        (root / "locations.tsv").write_text(
            "\n".join(f"{key}\t{value}" for key, value in sorted(entries.items())) + "\n"
        )

        selected = parse_locations(args.locations) if args.locations else sorted(entries)
        for loc in selected:
            list_payload = download_json(
                session,
                f"{BASE_URL}/products/types/FWS/locations/{loc}",
                root / "lists" / f"{loc}.json",
            )
            graph = list_payload.get("@graph", [])
            count = 0
            for item in graph:
                product_url = item.get("id") or item.get("@id")
                if not product_url:
                    continue
                product_id = product_url.rstrip("/").split("/")[-1]
                json_file = root / "products" / loc / f"{product_id}.json"
                txt_file = root / "products" / loc / f"{product_id}.txt"
                payload = download_json(session, f"{BASE_URL}/products/{product_id}", json_file)
                if not txt_file.exists():
                    txt_file.parent.mkdir(parents=True, exist_ok=True)
                    txt_file.write_text(payload.get("productText", ""))
                    print(f"[OK  ] {txt_file}")
                else:
                    print(f"[SKIP] {txt_file}")
                count += 1
                if args.max_products > 0 and count >= args.max_products:
                    break
            print(f"[INFO] {loc} {count} products")

    print("All done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
