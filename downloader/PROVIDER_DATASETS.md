# Provider Dataset Downloader

This extension adds catalog-driven raw downloads for provider-hosted hazard,
weather, fire, smoke, air-quality, drought, cyclone, and static-context sources.
It is intended for clients that need reproducible raw-data manifests before
building model-ready caches.

The downloader does not redistribute raw data. It records provider URLs,
download manifests, and clear instructions for sources that require credentials
or separate provider terms.

## Quick Start

List provider datasets:

```bash
python3 -m downloader.provider_cli --list
```

Dry-run a small request:

```bash
python3 -m downloader.provider_cli \
  --datasets aqs_pm25 hms_smoke ibtracs \
  --output-root ./downloads_demo \
  --start-year 2024 \
  --end-year 2024 \
  --dry-run \
  --max-files 3
```

Use a bounding box with FIRMS:

```bash
python3 -m downloader.provider_cli \
  --datasets firms_area \
  --output-root ./downloads_firms \
  --start-date 2024-06-01 \
  --end-date 2024-06-02 \
  --bbox=-125,32,-114,42 \
  --dry-run
```

Pass the FIRMS key through `FIRMS_MAP_KEY` or through per-dataset
`extra_options` in the Python API.

## Python API

```python
from downloader import ProviderDownloadRequest, download_provider_data

request = ProviderDownloadRequest(
    datasets=["aqs_pm25", "hms_smoke"],
    output_root="./downloads",
    years=(2024, 2025),
    dry_run=True,
)
results = download_provider_data(request)
```

## Implemented Sources

- `aqs_pm25`: EPA AirData hourly PM2.5 files and station metadata.
- `hms_smoke`: NOAA HMS annual smoke-polygon and fire-point bundles.
- `ibtracs`: NOAA/NCEI IBTrACS v04r01 CSV tracks and documentation.
- `hurdat2`: NOAA/NHC HURDAT2 best-track text files and format documents.
- `usdm`: U.S. Drought Monitor weekly GIS shapefile archive.
- `hrrr_fireseason`: NOAA HRRR public S3 files for selected fire-season dates.
- `wfigs_current`: current WFIGS perimeter snapshot through ArcGIS REST.
- `landfire_static`: known LF2024 CONUS `FBFM40` and `CC` static products.

## Credential or Terms-Limited Sources

- `firms_area`: requires a NASA FIRMS `MAP_KEY`.
- `merra2`: requires NASA Earthdata/GES DISC authenticated access.
- `landscan`: governed by ORNL/LandScan provider-specific access terms.
- `wrc_housing`: provider links can redirect/change; pass an explicit URL or use the provider portal.
- `mtbs_perimeters`: records provider instructions before heavy chunked ArcGIS pulls.

## Boundary

This is a raw-data downloader. It does not align grids, create training tensors,
or define model-ready splits. Downstream dataloaders should read the generated
manifests and provider files under the user's local data policy.
