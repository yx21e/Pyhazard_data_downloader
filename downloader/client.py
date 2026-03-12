from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
import json
import subprocess

from downloader.catalog import DATASETS, DatasetSpec


@dataclass(init=False)
class DownloadRequest:
    r"""Structured request input of :func:`downloader.download_data`.

    Args:
        datasets (Sequence[str]): Dataset ids to download.
        temporal_window (Tuple[str, str] | None, optional): Date range as
            ``("YYYY-MM-DD", "YYYY-MM-DD")``. Applied only to datasets with
            `time_mode != "none"`. (default: ``None``)
        area_of_interest_bbox (Tuple[float, float, float, float] | None, optional):
            Bounding box as ``(min_lon, min_lat, max_lon, max_lat)``. Applied
            only to datasets with `aoi_mode="native"` or `aoi_mode="postfilter"`.
            (default: ``None``)
        output_root (str, optional): Root directory for downloaded outputs.
            (default: ``"/home/yangshuang/output/downloader"``)
        extra_options (Dict[str, Dict[str, Any]] | None, optional): Per-dataset
            script options, for example
            ``{"nasa_gibs": {"layers": "MODIS_Terra_CorrectedReflectance_TrueColor"}}``.
            (default: ``None``)
    """

    datasets: Sequence[str]
    temporal_window: Optional[Tuple[str, str]]
    area_of_interest_bbox: Optional[Tuple[float, float, float, float]]
    output_root: str
    extra_options: Dict[str, Dict[str, Any]]

    def __init__(
        self,
        datasets: Sequence[str],
        temporal_window: Optional[Tuple[str, str]] = None,
        area_of_interest_bbox: Optional[Tuple[float, float, float, float]] = None,
        output_root: str = "/home/yangshuang/output/downloader",
        extra_options: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> None:
        self.datasets = datasets
        self.temporal_window = temporal_window
        self.area_of_interest_bbox = area_of_interest_bbox
        self.output_root = output_root
        self.extra_options = extra_options or {}


def list_datasets() -> List[Dict[str, Any]]:
    """Return dataset capability metadata for client-facing discovery."""
    rows = []
    for spec in DATASETS.values():
        rows.append(
            {
                "name": spec.name,
                "time_mode": spec.time_mode,
                "aoi_mode": spec.aoi_mode,
                "notes": spec.notes,
            }
        )
    return rows


def _bbox_to_area_string(bbox: Tuple[float, float, float, float]) -> str:
    min_lon, min_lat, max_lon, max_lat = bbox
    return f"{min_lon},{min_lat},{max_lon},{max_lat}"


def _build_command(root: Path, spec: DatasetSpec, request: DownloadRequest) -> tuple[List[str], List[str]]:
    cmd = ["python", str(root / "scripts" / spec.script)]
    warnings: List[str] = []
    out_dir = Path(request.output_root) / spec.name

    if spec.name == "historical_fires":
        cmd += ["--output-root", str(out_dir)]
    elif spec.name == "satellite_fire_detections_goes":
        cmd += ["--output-root", str(out_dir)]
    elif spec.name == "weather_forecast":
        cmd += ["--ndfd-dir", str(out_dir / "ndfd"), "--hrrr-dir", str(out_dir / "hrrr")]
    else:
        cmd += ["--output-dir", str(out_dir)]

    if request.temporal_window is not None:
        start, end = request.temporal_window
        if spec.time_mode == "range":
            cmd += ["--start-date", start, "--end-date", end]
        elif spec.time_mode == "year":
            if start[:4] != end[:4]:
                raise ValueError(f"{spec.name} expects a single-year temporal_window.")
            cmd += ["--year", start[:4]]
        elif spec.time_mode == "recent_window":
            warnings.append(
                f"{spec.name} does not accept explicit start/end dates; use extra_options to set recent-days if needed."
            )
        else:
            warnings.append(f"{spec.name} does not support temporal_window; parameter ignored.")

    if request.area_of_interest_bbox is not None:
        if spec.aoi_mode == "native":
            cmd.append(f"--area={_bbox_to_area_string(request.area_of_interest_bbox)}")
        elif spec.aoi_mode == "postfilter":
            warnings.append(
                f"{spec.name} does not subset during download; aoi_bbox should be applied after download."
            )
        else:
            warnings.append(f"{spec.name} does not support area_of_interest_bbox in downloader; parameter ignored.")

    for key, value in request.extra_options.get(spec.name, {}).items():
        flag = f"--{key.replace('_', '-')}"
        if isinstance(value, bool):
            if value:
                cmd.append(flag)
        else:
            cmd.extend([flag, str(value)])

    return cmd, warnings


def download_data(request: DownloadRequest) -> List[Dict[str, Any]]:
    """Run one or more downloader scripts through a unified client-facing API."""
    root = Path(__file__).resolve().parent
    results = []

    for raw_name in request.datasets:
        name = str(raw_name).strip().lower()
        if name not in DATASETS:
            raise KeyError(f"Unknown dataset: {raw_name}")

        spec = DATASETS[name]
        cmd, request_warnings = _build_command(root, spec, request)
        proc = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True)

        results.append(
            {
                "dataset": spec.name,
                "time_mode": spec.time_mode,
                "aoi_mode": spec.aoi_mode,
                "status": "pass" if proc.returncode == 0 else "fail",
                "returncode": proc.returncode,
                "command": cmd,
                "output_dir": str(Path(request.output_root) / spec.name),
                "applied_temporal_window": request.temporal_window if spec.time_mode in ("range", "year") else None,
                "applied_aoi_bbox": request.area_of_interest_bbox if spec.aoi_mode == "native" else None,
                "warnings": request_warnings,
                "stdout_tail": proc.stdout[-2000:],
                "stderr_tail": proc.stderr[-2000:],
            }
        )
    return results


def save_download_report(results: Sequence[Dict[str, Any]], output_path: str) -> str:
    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(list(results), indent=2), encoding="utf-8")
    return str(path)
