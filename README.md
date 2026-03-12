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
  - `canopy_cover`: LANDFIRE canopy cover raster
  - `current_perimeters`: current WFIGS fire perimeter snapshot
  - `goes_geocolor`: GOES GeoColor source imagery files
  - `historical_fires`: historical fire perimeter archives
  - `hpwren_real_time_weather_stations`: HPWREN station metadata and recent samples
  - `nasa_gibs`: NASA GIBS global imagery layers
  - `nohrsc_snow_analysis`: NOHRSC daily snow analysis archives
  - `satellite_fire_detections_goes`: GOES fire detection files
  - `satellite_fire_detections_modis`: FIRMS MODIS fire detection CSV
  - `satellite_fire_detections_viirs`: FIRMS VIIRS fire detection CSV
  - `smoke_analysis`: HMS annual smoke polygon bundle
  - `spot_forecast`: current and recent spot forecast products
  - `surface_fuels`: LANDFIRE surface fuels raster
  - `vegetation_type`: LANDFIRE vegetation type raster
  - `watches_and_warnings`: NDFD watches and warnings files
  - `weather_forecast`: NDFD and HRRR forecast files
  - `wrc_housing_density`: WRC housing density raster

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
