# FireWx-FM Data Source Coverage

This page summarizes which public data resources used around FireWx-FM are
covered by this downloader. The package downloads raw provider files and writes
manifests. It does not redistribute provider data, build model-ready grids, or
release project-specific cached tensors.

## Core FireWx-FM Sources

| Role | Provider resource | Native granularity | Downloader id | Status |
|---|---|---:|---|---|
| Dynamic weather | NOAA HRRR surface forecast files | Native HRRR CONUS files; configured fire-season cycles | `hrrr_fireseason` | Auto-download from public NOAA S3 |
| Active-fire supervision | NASA FIRMS area API | Point detections by satellite over requested dates/AOI | `firms_area` | Credentialed API; requires `FIRMS_MAP_KEY` |
| Fuel model | LANDFIRE FBFM40 | Static CONUS raster product | `landfire_static` | Auto-download for known LF2024 URL |
| Canopy cover | LANDFIRE CC | Static CONUS raster product | `landfire_static` | Auto-download for known LF2024 URL |
| Housing exposure | Wildfire Risk to Communities housing-unit density | Static CONUS raster product | `wrc_housing` | Auto-download with provider URL; URL override supported |
| Population exposure | LandScan | Static gridded population product | `landscan` | Instruction manifest; provider terms required |

## Pretrained Input Channel Contract

The released FireWx-FM checkpoints expect a fixed 16-channel tensor in
`[channel, y, x]` order. Channel order is part of the checkpoint contract.
The California 5 km, 12-hour-lead cache records the weather names
`[t2m, d2m, u10, v10, cape, sp, blh, vis, prate, tp]` and the static names
`[fuel_fbfm40, canopy_cover, housing_density, population]`.

The released California checkpoints use native source units with no mean/std
normalization, min/max scaling, or unit conversion. Invalid or missing values
are zero-filled before inference. New retraining runs can enable normalization
in the training config, but that does not change the released checkpoint
contract.

| Channel | Name | Dataset/source | Level or selection | Units | Role |
|---:|---|---|---|---|---|
| 0 | `t2m` | NOAA HRRR | 2 m above ground | K | 2 m temperature |
| 1 | `d2m` | NOAA HRRR | 2 m above ground | K | 2 m dew point |
| 2 | `u10` | NOAA HRRR | 10 m above ground | m/s | 10 m east-west wind component |
| 3 | `v10` | NOAA HRRR | 10 m above ground | m/s | 10 m north-south wind component |
| 4 | `cape` | NOAA HRRR | surface, instant | J/kg | Surface instantaneous CAPE |
| 5 | `sp` | NOAA HRRR | surface, instant | Pa | Surface pressure |
| 6 | `blh` | NOAA HRRR | surface diagnostic, instant | m | Boundary-layer height |
| 7 | `vis` | NOAA HRRR | surface diagnostic, instant | m | Visibility |
| 8 | `prate` | NOAA HRRR | surface, instant | kg m^-2 s^-1 | Precipitation rate |
| 9 | `tp` | NOAA HRRR | surface, accumulated | kg m^-2 | Accumulated precipitation |
| 10 | `firewx_valid` | Cache validity channel | input presence | binary mask | Cache-level dynamic input presence mask; 1.0 everywhere in this release |
| 11 | `static_valid` | Static reprojection mask | static layers | fraction | Fraction of static layers valid at the grid cell |
| 12 | `fuel_fbfm40` | LANDFIRE FBFM40 | static layer | categorical code | Fire-behavior fuel model |
| 13 | `canopy_cover` | LANDFIRE CC | static layer | provider-native value | Canopy cover |
| 14 | `housing_density` | Wildfire Risk to Communities | static layer | provider-native value | Housing-unit density |
| 15 | `population` | LandScan Global 2024 | static layer | provider-native value | Population exposure |

NASA FIRMS detections are used to derive the occupancy target, not as an input
channel. WFIGS and MTBS are event-level resources for supporting tasks and are
not part of the 16-channel pretrained occupancy input.

The `cape` channel is the HRRR surface instantaneous CAPE field selected with
`typeOfLevel=surface` and `stepType=instant`; it is not most-unstable CAPE or a
layer CAPE variable.

The two validity channels have different definitions. `firewx_valid` is a
cache-level dynamic input presence mask; in the released California regional
cache it is 1.0 everywhere and is not a per-variable HRRR missing-data mask.
`static_valid` is the fraction of the four static layers valid after
reprojection at each grid cell, with possible values 0.0, 0.25, 0.5, 0.75, and
1.0.

Static raster resampling into the FireWx-FM 5 km grid is model-preparation
logic, not downloader logic. In the released cache builder, LANDFIRE FBFM40 and
LANDFIRE canopy cover use nearest-neighbor resampling, while WRC housing density
and LandScan population use bilinear resampling.

Example dry run for the core public/credentialed sources:

```bash
python3 -m downloader.provider_cli \
  --datasets hrrr_fireseason firms_area landfire_static wrc_housing landscan \
  --output-root ./downloads_firewx \
  --start-year 2024 \
  --end-year 2024 \
  --start-date 2024-06-01 \
  --end-date 2024-06-02 \
  --bbox=-125,32,-114,42 \
  --dry-run \
  --max-files 4
```

Set `FIRMS_MAP_KEY` before running a real FIRMS request. Keep downloaded raw
provider files and credentials outside git.

For custom HRRR date/hour/forecast-hour requests, use:

```bash
python3 downloader/scripts/hrrr_downloader.py \
  --start-date 2024-06-01 \
  --end-date 2024-06-02 \
  --hours 00,06,12,18 \
  --forecast-hours 00 \
  --output-root ./downloads_hrrr \
  --include-idx \
  --dry-run
```

Remove `--dry-run` for real downloads. Use `--idx-only --max-files 1` for a
small live smoke test.

## Event-Level and Supporting Wildfire Sources

| Role | Provider resource | Native granularity | Downloader entry | Status |
|---|---|---:|---|---|
| Current perimeter snapshot | WFIGS Interagency Perimeters Current | Current ArcGIS feature layer | `wfigs_current` | Auto-download through ArcGIS REST |
| Historical incident/perimeter attributes | WFIGS Interagency Perimeters | ArcGIS features over requested date range | `historical_fires` script | Auto-download through script-backed client |
| California historical perimeters | FRAP fire perimeters | Vector perimeter archive | `historical_fires` script | Auto-download through script-backed client |
| Historical GeoMAC perimeters | GeoMAC perimeter archives | Vector perimeter archives | `historical_fires` script | Auto-download through script-backed client |
| Burned-area outcomes | MTBS perimeter/severity records | Event and perimeter products | `mtbs_perimeters` | Instruction manifest for public source; heavy chunked pull should be staged |

The event-level sources are useful for burned-area, analog, and audit tasks.
They are not used as occupancy labels for FireWx-FM.

## Broader Hazard and Environmental Inventory

| Family | Provider resource | Downloader entry | Status |
|---|---|---|---|
| Forecast weather | NDFD and HRRR forecast files | `weather_forecast` script | Auto-download; uses public NOAA buckets |
| Reanalysis weather | NASA MERRA-2 | `merra2` | Instruction manifest; Earthdata/GES DISC credentials required |
| GOES fire detections | GOES ABI-L2-FDCF | `satellite_fire_detections_goes` script | Auto-download; uses public NOAA buckets and AWS CLI |
| GOES imagery | GOES ABI-L2-MCMIPC | `goes_geocolor` script | Auto-download; uses public NOAA buckets |
| Smoke | NOAA HMS smoke and fire bundles | `hms_smoke` | Auto-download |
| Air quality | EPA AQS hourly PM2.5 | `aqs_pm25` | Auto-download |
| Drought | U.S. Drought Monitor GIS archive | `usdm` | Auto-download |
| Tropical cyclone | IBTrACS and HURDAT2 | `ibtracs`, `hurdat2` | Auto-download |

Use `python3 -m downloader.provider_cli --list` for the current provider
catalog. Use `python3 example_downloader_client.py` for the older script-backed
entry point.

## What This Downloader Does Not Do

- It does not crop, reproject, or align sources onto the FireWx-FM grid; that
  step belongs to downstream data preparation.
- It does not create train/validation/test splits.
- It does not release raw provider data or project-local cached data.
- It does not bypass provider credentials, licenses, or access controls.
