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

| Channel | Name | Dataset/source | Role |
|---:|---|---|---|
| 0 | `t2m` | NOAA HRRR | 2 m temperature |
| 1 | `d2m` | NOAA HRRR | 2 m dew point |
| 2 | `u10` | NOAA HRRR | 10 m east-west wind component |
| 3 | `v10` | NOAA HRRR | 10 m north-south wind component |
| 4 | `cape` | NOAA HRRR | Convective available potential energy |
| 5 | `sp` | NOAA HRRR | Surface pressure |
| 6 | `blh` | NOAA HRRR | Boundary-layer height |
| 7 | `vis` | NOAA HRRR | Visibility |
| 8 | `prate` | NOAA HRRR | Precipitation rate |
| 9 | `tp` | NOAA HRRR | Accumulated precipitation |
| 10 | `firewx_valid` | Cache validity channel | Dynamic/input validity mask for this regional cache |
| 11 | `static_valid` | Static reprojection mask | Fraction of static layers valid at the grid cell |
| 12 | `fuel_fbfm40` | LANDFIRE FBFM40 | Fire-behavior fuel model |
| 13 | `canopy_cover` | LANDFIRE CC | Canopy cover |
| 14 | `housing_density` | Wildfire Risk to Communities | Housing-unit density |
| 15 | `population` | LandScan Global 2024 | Population exposure |

NASA FIRMS detections are used to derive the occupancy target, not as an input
channel. WFIGS and MTBS are event-level resources for supporting tasks and are
not part of the 16-channel pretrained occupancy input.

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
