#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Download HPWREN weather station metadata, realtime feed, and recent historical samples.

Usage:
    python hpwren_real_time_weather_stations.py
    python hpwren_real_time_weather_stations.py --recent-days 3
"""

import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
import urllib3

urllib3.disable_warnings()

# ===== USER SETTINGS =====
RECENT_DAYS = float(os.environ.get("HPWREN_RECENT_DAYS", "1"))
OUTPUT_DIR = "./downloads/hpwren_real_time_weather_stations"
SITES_JS_URL = "https://www.hpwren.ucsd.edu/cameras/sites.js"
REALTIME_URL = "https://cdn.hpwren.ucsd.edu/RT/wxtcf.json"
HISTORY_URL = "https://x73i7ddjsldppoannzahvrqmqy0vgflz.lambda-url.us-west-2.on.aws/"


def download_text(session: requests.Session, url: str, out_file: Path, params=None):
    if out_file.exists():
        print(f"[SKIP] {out_file}")
        return out_file.read_text()

    out_file.parent.mkdir(parents=True, exist_ok=True)
    print(f"[GET ] {url}")
    response = session.get(url, params=params, timeout=180, verify=False)
    response.raise_for_status()
    tmp = out_file.with_suffix(out_file.suffix + ".part")
    tmp.write_text(response.text)
    tmp.replace(out_file)
    print(f"[OK  ] {out_file}")
    return out_file.read_text()


def parse_sites(raw_js: str):
    payload = raw_js.split("var sites =", 1)[1].rsplit(";", 1)[0]
    return json.loads(payload)


def main():
    parser = argparse.ArgumentParser(description="Download HPWREN weather metadata and recent samples.")
    parser.add_argument("--recent-days", type=float, default=RECENT_DAYS, help="Recent history window in days")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="Output directory")
    args = parser.parse_args()

    root = Path(args.output_dir)

    with requests.Session() as session:
        session.headers["User-Agent"] = "firemap-hpwren-downloader/1.0"

        raw_sites = download_text(session, SITES_JS_URL, root / "metadata" / "sites.js")
        sites = parse_sites(raw_sites)

        active_met = {}
        for site_code, site in sites.items():
            for sensor_id, sensor in site.get("sensors", {}).items():
                if sensor.get("type") == "met" and sensor.get("active") == "y":
                    active_met[sensor_id] = {
                        "site_code": site_code,
                        "site_name": site.get("name"),
                        "lat": site.get("lat"),
                        "lon": site.get("long"),
                        "elev": site.get("elev"),
                        "sensor": sensor,
                    }

        sensors_file = root / "metadata" / "active_met_sensors.json"
        sensors_file.parent.mkdir(parents=True, exist_ok=True)
        sensors_file.write_text(json.dumps(active_met, indent=2, sort_keys=True))
        print(f"[OK  ] {sensors_file}")

        note_file = root / "metadata" / "availability_note.txt"
        note_file.write_text(
            "This public downloader stores station metadata, the realtime summary feed, and a recent sample window.\n"
            "Older full-history access from the public endpoint is limited/unstable.\n"
        )
        print(f"[OK  ] {note_file}")

        download_text(session, REALTIME_URL, root / "realtime" / "wxtcf.json")

        recent_end = datetime.now(timezone.utc).replace(microsecond=0)
        recent_start = recent_end - timedelta(days=args.recent_days)
        sample_dir = root / "recent_samples" / recent_start.strftime("%Y-%m-%d")

        for sensor_id in sorted(active_met):
            download_text(
                session,
                HISTORY_URL,
                sample_dir / f"{sensor_id}.json",
                params={
                    "site_id": sensor_id,
                    "start": int(recent_start.timestamp()),
                    "end": int(recent_end.timestamp()),
                },
            )

    print("All done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
