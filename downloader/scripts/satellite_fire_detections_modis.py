#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from datetime import date, timedelta
from pathlib import Path

import requests

DEFAULT_MAP_KEY = os.environ.get('FIRMS_MAP_KEY')
DEFAULT_AREA = os.environ.get('FIRMS_AREA', '-125,24,-66,50')
BASE_URL = 'https://firms.modaps.eosdis.nasa.gov/api/area/csv'
OUTPUT_DIR = Path(os.environ.get('FIRMS_OUTPUT_DIR', './downloads/firms'))
SOURCES = {
    'MODIS_SP': 'MODIS_SP',
    'MODIS_URT_NRT': 'MODIS_NRT',
}


def iter_days(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def main() -> int:
    parser = argparse.ArgumentParser(description='Download FIRMS MODIS CSV files.')
    parser.add_argument('--start-date', default=os.environ.get('FIRMS_START_DATE', '2024-01-01'))
    parser.add_argument('--end-date', default=os.environ.get('FIRMS_END_DATE', '2024-12-31'))
    parser.add_argument('--map-key', default=DEFAULT_MAP_KEY)
    parser.add_argument('--area', default=DEFAULT_AREA)
    parser.add_argument('--day-range', default=os.environ.get('FIRMS_DAY_RANGE', '1'))
    parser.add_argument('--output-dir', default=str(OUTPUT_DIR))
    args = parser.parse_args()
    if not args.map_key:
        raise SystemExit('FIRMS MAP_KEY is required. Set FIRMS_MAP_KEY or pass --map-key.')

    start = date.fromisoformat(args.start_date)
    end = date.fromisoformat(args.end_date)
    output_dir = Path(args.output_dir)

    with requests.Session() as session:
        session.headers['User-Agent'] = 'firemap-modis-downloader/1.0'
        for day in iter_days(start, end):
            print(f'=== {day.isoformat()} ===')
            for folder, api_name in SOURCES.items():
                out_file = output_dir / folder / f'{day.isoformat()}.csv'
                if out_file.exists():
                    print(f'[skip] {out_file}')
                    continue
                url = f'{BASE_URL}/{args.map_key}/{api_name}/{args.area}/{args.day_range}/{day.isoformat()}'
                print(f'[get ] {url}')
                response = session.get(url, stream=True, timeout=120)
                if not response.ok:
                    print(f'[fail] HTTP {response.status_code} -> {url}')
                    continue
                out_file.parent.mkdir(parents=True, exist_ok=True)
                tmp = out_file.with_suffix(out_file.suffix + '.part')
                with tmp.open('wb') as fh:
                    for chunk in response.iter_content(1024 * 1024):
                        if chunk:
                            fh.write(chunk)
                tmp.replace(out_file)
                print(f'[ok  ] {out_file}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
