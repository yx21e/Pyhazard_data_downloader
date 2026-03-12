# Pyhazard Data Downloader

Unified client-facing downloader for multi-source hazard and environmental datasets.

## Main API

```python
from downloader import DownloadRequest, download_data, list_datasets
```

```python
request = DownloadRequest(
    datasets=["satellite_fire_detections_viirs", "nasa_gibs", "current_perimeters"],
    temporal_window=("2024-01-01", "2024-01-01"),
    area_of_interest_bbox=(-125.0, 24.0, -66.0, 50.0),
    output_root="/home/yangshuang/output/downloader_example",
    extra_options={
        "nasa_gibs": {"layers": "MODIS_Terra_CorrectedReflectance_TrueColor"},
        "satellite_fire_detections_viirs": {"day_range": 1},
    },
)

results = download_data(request)
```

## `DownloadRequest` Parameters

- `datasets: list[str]`
  Supported values:
  - `canopy_cover`
  - `current_perimeters`
  - `goes_geocolor`
  - `historical_fires`
  - `hpwren_real_time_weather_stations`
  - `nasa_gibs`
  - `nohrsc_snow_analysis`
  - `satellite_fire_detections_goes`
  - `satellite_fire_detections_modis`
  - `satellite_fire_detections_viirs`
  - `smoke_analysis`
  - `spot_forecast`
  - `surface_fuels`
  - `vegetation_type`
  - `watches_and_warnings`
  - `weather_forecast`
  - `wrc_housing_density`

- `temporal_window: tuple[str, str] | None`
  Format:
  - `("YYYY-MM-DD", "YYYY-MM-DD")`

- `area_of_interest_bbox: tuple[float, float, float, float] | None`
  Format:
  - `(min_lon, min_lat, max_lon, max_lat)`

- `output_root: str`
  Meaning:
  - root directory where each dataset writes its own subfolder

- `extra_options: dict[str, dict]`
  Meaning:
  - per-dataset script options

## Capability Model

Each dataset declares:

- `time_mode`
  - `none`
  - `range`
  - `year`
  - `recent_window`

- `aoi_mode`
  - `unsupported`
  - `native`
  - `postfilter`

This is more accurate than pretending every downloader supports identical query semantics.

## Output

`download_data(request)` returns a list of structured records:

- `dataset`
- `status`
- `returncode`
- `command`
- `output_dir`
- `applied_temporal_window`
- `applied_aoi_bbox`
- `warnings`
- `stdout_tail`
- `stderr_tail`

## Files

- `downloader/`
  - main package
- `downloader/scripts/`
  - raw downloader scripts
- `example_downloader_client.py`
  - minimal client example
- `verify_downloader_readiness.py`
  - batch verification entrypoint

## Install

```bash
pip install -r requirements.txt
```
