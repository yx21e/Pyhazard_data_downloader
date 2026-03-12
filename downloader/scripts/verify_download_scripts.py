from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path("/home/yangshuang/download_scripts")
OUT_ROOT = Path("/home/yangshuang/output/download_script_checks")
OUT_ROOT.mkdir(parents=True, exist_ok=True)


CASES = [
    {
        "name": "canopy_cover",
        "cmd": ["python", "canopy_cover.py", "--version", "LF2024", "--output-dir", str(OUT_ROOT / "canopy_cover")],
        "timeout": 300,
    },
    {
        "name": "current_perimeters",
        "cmd": ["python", "current_perimeters.py", "--output-dir", str(OUT_ROOT / "current_perimeters")],
        "timeout": 180,
    },
    {
        "name": "goes_geocolor",
        "cmd": [
            "python",
            "goes_geocolor.py",
            "--start-date",
            "2024-01-01",
            "--end-date",
            "2024-01-01",
            "--hour",
            "18",
            "--sats",
            "G16",
            "--output-dir",
            str(OUT_ROOT / "goes_geocolor"),
        ],
        "timeout": 240,
    },
    {
        "name": "historical_fires",
        "cmd": [
            "python",
            "historical_fires.py",
            "--start-date",
            "2024-07-01",
            "--end-date",
            "2024-07-02",
            "--skip-frap",
            "--skip-geomac",
            "--output-root",
            str(OUT_ROOT / "historical_fires"),
        ],
        "timeout": 240,
    },
    {
        "name": "hpwren_real_time_weather_stations",
        "cmd": [
            "python",
            "hpwren_real_time_weather_stations.py",
            "--recent-days",
            "0.02",
            "--output-dir",
            str(OUT_ROOT / "hpwren_real_time_weather_stations"),
        ],
        "timeout": 240,
    },
    {
        "name": "nasa_gibs",
        "cmd": [
            "python",
            "nasa_gibs.py",
            "--start-date",
            "2024-01-01",
            "--end-date",
            "2024-01-01",
            "--layers",
            "MODIS_Terra_CorrectedReflectance_TrueColor",
            "--output-dir",
            str(OUT_ROOT / "nasa_gibs"),
        ],
        "timeout": 240,
    },
    {
        "name": "nohrsc_snow_analysis",
        "cmd": [
            "python",
            "nohrsc_snow_analysis.py",
            "--start-date",
            "2024-01-01",
            "--end-date",
            "2024-01-01",
            "--output-dir",
            str(OUT_ROOT / "nohrsc_snow_analysis"),
        ],
        "timeout": 240,
    },
    {
        "name": "satellite_fire_detections_goes",
        "cmd": [
            "python",
            "satellite_fire_detections_goes.py",
            "--start-date",
            "2024-01-01",
            "--end-date",
            "2024-01-01",
            "--sats",
            "G16",
            "--output-root",
            str(OUT_ROOT / "satellite_fire_detections_goes"),
        ],
        "timeout": 300,
    },
    {
        "name": "satellite_fire_detections_modis",
        "cmd": [
            "python",
            "satellite_fire_detections_modis.py",
            "--start-date",
            "2024-01-01",
            "--end-date",
            "2024-01-01",
            "--output-dir",
            str(OUT_ROOT / "satellite_fire_detections_modis"),
        ],
        "timeout": 240,
    },
    {
        "name": "satellite_fire_detections_viirs",
        "cmd": [
            "python",
            "satellite_fire_detections_viirs.py",
            "--start-date",
            "2024-01-01",
            "--end-date",
            "2024-01-01",
            "--output-dir",
            str(OUT_ROOT / "satellite_fire_detections_viirs"),
        ],
        "timeout": 240,
    },
    {
        "name": "smoke_analysis",
        "cmd": ["python", "smoke_analysis.py", "--year", "2024", "--output-dir", str(OUT_ROOT / "smoke_analysis")],
        "timeout": 300,
    },
    {
        "name": "spot_forecast",
        "cmd": [
            "python",
            "spot_forecast.py",
            "--locations",
            "LOX",
            "--max-products",
            "1",
            "--output-dir",
            str(OUT_ROOT / "spot_forecast"),
        ],
        "timeout": 240,
    },
    {
        "name": "surface_fuels",
        "cmd": ["python", "surface_fuels.py", "--version", "LF2024", "--output-dir", str(OUT_ROOT / "surface_fuels")],
        "timeout": 300,
    },
    {
        "name": "vegetation_type",
        "cmd": ["python", "vegetation_type.py", "--version", "LF2024", "--output-dir", str(OUT_ROOT / "vegetation_type")],
        "timeout": 300,
    },
    {
        "name": "watches_and_warnings",
        "cmd": [
            "python",
            "watches_and_warnings.py",
            "--start-date",
            "2024-01-01",
            "--end-date",
            "2024-01-01",
            "--output-dir",
            str(OUT_ROOT / "watches_and_warnings"),
        ],
        "timeout": 240,
    },
    {
        "name": "weather_forecast",
        "cmd": [
            "python",
            "weather_forecast.py",
            "--start-date",
            "2024-01-01",
            "--end-date",
            "2024-01-01",
            "--ndfd-vars",
            "maxt",
            "--hrrr-cycles",
            "00",
            "--ndfd-dir",
            str(OUT_ROOT / "weather_forecast" / "ndfd"),
            "--hrrr-dir",
            str(OUT_ROOT / "weather_forecast" / "hrrr"),
        ],
        "timeout": 300,
    },
    {
        "name": "wrc_housing_density",
        "cmd": ["python", "wrc_housing_density.py", "--output-dir", str(OUT_ROOT / "wrc_housing_density")],
        "timeout": 300,
    },
]


def _count_files(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for p in path.rglob("*") if p.is_file())


def run_case(case: dict) -> dict:
    name = case["name"]
    output_hint = Path(case["cmd"][-1]) if case["cmd"][-2].startswith("--output") or case["cmd"][-2].endswith("-dir") else OUT_ROOT / name
    before = _count_files(output_hint.parent if output_hint.suffix else output_hint)
    try:
        result = subprocess.run(
            case["cmd"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=case["timeout"],
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        status = "pass" if result.returncode == 0 else "fail"
        error = None
    except subprocess.TimeoutExpired as exc:
        result = exc
        status = "timeout"
        error = "timeout"

    after = _count_files(output_hint.parent if output_hint.suffix else output_hint)
    created_files = max(after - before, 0)

    stdout = result.stdout if hasattr(result, "stdout") and result.stdout else ""
    stderr = result.stderr if hasattr(result, "stderr") and result.stderr else ""
    returncode = result.returncode if hasattr(result, "returncode") else None

    if status == "pass" and created_files == 0:
        status = "fail"
        error = "no_files_created"

    return {
        "name": name,
        "status": status,
        "returncode": returncode,
        "created_files": created_files,
        "output_dir": str(output_hint.parent if output_hint.suffix else output_hint),
        "stdout_tail": stdout[-2000:],
        "stderr_tail": stderr[-2000:],
        "error": error,
    }


def main() -> int:
    results = []
    for case in CASES:
        print(f"[RUN] {case['name']}")
        results.append(run_case(case))

    report_path = OUT_ROOT / "download_script_report.json"
    report_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print("\ndownload script summary")
    for item in results:
        print(
            f"- {item['name']}: {item['status'].upper()} | "
            f"returncode={item['returncode']} created_files={item['created_files']} error={item['error']}"
        )
    print(f"report saved: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
