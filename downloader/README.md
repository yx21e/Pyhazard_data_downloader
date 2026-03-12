# Downloader

Unified client-facing interface for dataset download scripts.

## Main API

```python
from downloader import DownloadRequest, download_data, list_datasets
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
  Meaning:
  - applied only when the selected dataset supports time selection

- `area_of_interest_bbox: tuple[float, float, float, float] | None`
  Format:
  - `(min_lon, min_lat, max_lon, max_lat)`
  Meaning:
  - applied only when the selected dataset supports AOI selection

- `output_root: str`
  Meaning:
  - root directory where each dataset writes its own subfolder

- `extra_options: dict[str, dict]`
  Meaning:
  - per-dataset script options
  Example:
  - `{"nasa_gibs": {"layers": "MODIS_Terra_CorrectedReflectance_TrueColor"}}`

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

This is more accurate than pretending every downloader supports the same query semantics.

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

## Example

```python
from downloader import DownloadRequest, download_data, save_download_report

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
save_download_report(results, "/home/yangshuang/output/downloader_example/report.json")
```

## Notes

- Datasets with `aoi_mode="unsupported"` ignore `area_of_interest_bbox` and return a warning.
- Datasets with `time_mode="none"` ignore `temporal_window` and return a warning.
- Static products such as LANDFIRE and WRC are full-product downloads.
