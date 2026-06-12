# Wildfire Foundation Model and Downloader Handoff

Date: 2026-06-12

This handoff summarizes the current release state for the trained wildfire
reference model, the provider-data downloader, and the next pipeline needed for
a broader foundation-model retraining workflow.

## Current Release State

### Trained WildFIRE-FM checkpoints

The trained WildFIRE-FM reference checkpoints are uploaded to the Hugging Face
Hub repository:

```text
https://huggingface.co/RAI-Lab/Wildfire-FM
```

Remote checkpoint files confirmed on 2026-06-12:

| Seed | Hub path | Size |
|---:|---|---:|
| 1 | `models/wildfire_fm/checkpoints/seed_1/best_firms_prauc.pt` | 31,092,197 bytes |
| 7 | `models/wildfire_fm/checkpoints/seed_7/best_firms_prauc.pt` | 31,092,197 bytes |
| 42 | `models/wildfire_fm/checkpoints/seed_42/best_firms_prauc.pt` | 31,092,197 bytes |
| 99 | `models/wildfire_fm/checkpoints/seed_99/best_firms_prauc.pt` | 31,092,197 bytes |
| 123 | `models/wildfire_fm/checkpoints/seed_123/best_firms_prauc.pt` | 31,092,197 bytes |

The local release workspace stores checkpoint metadata, configs, metrics, and
model code, but not the `.pt` files themselves. Treat Hugging Face as the source
of truth for released weights.

Important local metadata files in the release workspace:

```text
models/wildfire_fm/checkpoint_manifest.json
models/wildfire_fm/modeling_unet.py
models/wildfire_fm/configs/reference_fireprone_seed_*.json
models/wildfire_fm/metrics/reference_fireprone_seed_*/run_summary.json
```

### Downloader repository

The downloader work belongs to:

```text
https://github.com/yx21e/Pyhazard_data_downloader
```

The current downloader repository has two compatible paths:

- The original script-backed downloader for operational hazard products.
- The new provider-catalog downloader for foundation-model raw data sources.

The provider-catalog downloader was added in commit:

```text
6d374c0 Add provider catalog downloader
```

Main new files:

```text
downloader/provider_catalog.py
downloader/provider_client.py
downloader/provider_sources.py
downloader/provider_cli.py
downloader/PROVIDER_DATASETS.md
example_provider_downloader_client.py
```

The evaluation-contract paper repository was briefly updated by mistake and was
then reverted. It should not be treated as the home for the downloader.

## What the Current WildFIRE-FM Is

WildFIRE-FM is the trained wildfire-specialized reference model used for the
fixed-contract comparisons. It is not yet a general multi-hazard foundation
model.

Current model contract:

- Region: California regional grid.
- Grid: 5 km projected grid in EPSG:5070.
- Dynamic cadence: weather fields every 6 hours.
- Forecast lead: 12-hour wildfire occupancy.
- Input: 16 channels.
- Dynamic weather inputs: 10 weather fields from HRRR-derived regional data.
- Static context: LANDFIRE fuel model, LANDFIRE canopy cover, WRC housing-unit
  density, and LandScan population.
- Masks: weather validity and static-context validity masks.
- Supervision: FIRMS-derived gridded active-fire occupancy.
- Split: June-August 2024 training, September 2024 validation, October 2024
  testing.
- Architecture: compact U-Net with occupancy output and auxiliary spatial
  support output.

WFIGS and MTBS are used for supporting event-level and burned-area tasks, but
they are not the main occupancy labels for this released backbone.

## Provider-Catalog Downloader

The provider-catalog downloader is a raw-data downloader. It does not align
grids, create training tensors, or redistribute raw provider data.

List sources:

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

Python API:

```python
from downloader import ProviderDownloadRequest, download_provider_data

request = ProviderDownloadRequest(
    datasets=["aqs_pm25", "hms_smoke", "ibtracs"],
    output_root="./downloads_demo",
    years=(2024, 2024),
    dry_run=True,
    max_files=2,
)
results = download_provider_data(request)
```

Currently cataloged provider sources:

```text
aqs_pm25
firms_area
hms_smoke
hrrr_fireseason
hurdat2
ibtracs
landfire_static
landscan
merra2
mtbs_perimeters
usdm
wfigs_current
wrc_housing
```

Credential or terms-limited sources are explicit:

- `firms_area` requires a NASA FIRMS `MAP_KEY`.
- `merra2` requires NASA Earthdata/GES DISC access.
- `landscan` requires ORNL/LandScan provider-specific access.
- `wrc_housing` may require an explicit current provider URL.
- `mtbs_perimeters` currently records provider instructions rather than
  launching heavy chunked pulls.

## Verified Commands

These checks passed before this handoff was written:

```bash
python3 -m downloader.provider_cli --list
python3 example_provider_downloader_client.py
python3 -m py_compile downloader/*.py downloader/scripts/*.py \
  example_downloader_client.py example_provider_downloader_client.py \
  verify_downloader_readiness.py
```

The provider dry-run path was also checked with:

```bash
python3 -m downloader.provider_cli \
  --datasets aqs_pm25 hms_smoke ibtracs mtbs_perimeters \
  --output-root /tmp/pyhazard_provider_smoke \
  --start-year 2024 \
  --end-year 2024 \
  --dry-run \
  --max-files 2
```

Expected statuses:

- `aqs_pm25`: `pass`
- `hms_smoke`: `pass`
- `ibtracs`: `pass`
- `mtbs_perimeters`: `instructions_only`

FIRMS without a key should return `auth_required`, not fail silently.

## Next Pipeline

### Stage 1: Keep the released wildfire reference stable

Do not retrain or relabel the released WildFIRE-FM checkpoints unless the goal is
to create a new model version. The current Hugging Face weights are the released
reference.

Minimum checks before citing or using the released model:

1. Confirm the five `.pt` files exist on Hugging Face.
2. Confirm the checkpoint manifest lists the same five seeds and byte sizes.
3. Load `modeling_unet.py` and one checkpoint in a local environment with
   PyTorch.
4. Record the exact Hub commit or snapshot if a downstream result depends on it.

### Stage 2: Use downloader only for raw provider data

For client-facing data acquisition:

1. Use `python3 -m downloader.provider_cli --list` to select sources.
2. Run `--dry-run --max-files` first.
3. Store downloaded provider files under a user-controlled raw-data root.
4. Keep generated `download_manifest.json` files with the raw files.
5. Do not commit raw provider data or credentials.

The downloader should remain provider-compliant and transparent. It should not
pretend to bypass authentication, terms of use, or missing observations.

### Stage 3: Build adapter layer before retraining

The next foundation-model work needs a model-ready adapter layer between raw
downloads and training.

Required registries:

- `sources.yml`: provider, access mode, citation, native cadence, and terms.
- `variables.yml`: canonical variable names, units, transforms, masks.
- `grids.yml`: CRS, resolution, extent, and regridding rule.
- `tasks.yml`: target type, prediction unit, metric family, observation mask.
- `splits.yml`: chronological, event-level, or geography-aware split policy.

Required sample interface:

```text
SampleRecord
  sample_id
  source_id
  task_family
  region
  grid_spec
  time_context
  lead_times
  dynamic_fields
  static_fields
  dynamic_valid_mask
  static_valid_mask
  targets
  target_valid_mask
  event_metadata
  provenance
```

First adapter target: rebuild the current FireWx-FM 16-channel occupancy samples
from local provider-prepared data. This must reproduce the released data contract
before adding non-wildfire tasks.

### Stage 4: General foundation-model retraining

The next model should not be "FireWx-FM plus more labels." It should be a
general spatiotemporal hazard/Earth backbone with task-specific heads.

Recommended order:

1. Rebuild current FireWx-FM samples through the adapter interface.
2. Add dense environmental objectives from HRRR or MERRA-2 style fields.
3. Attach the wildfire occupancy head and compare against released WildFIRE-FM.
4. Add high-readiness downstream heads:
   - smoke or PM2.5 from HMS/AQS;
   - extreme heat from dense weather fields;
   - drought from USDM;
   - cyclone track/intensity from IBTrACS/HURDAT2.
5. Only add flood or burn-severity raster branches after label pipelines are
   independently audited.

Evaluation rule:

- Keep wildfire fixed-contract metrics unchanged for comparability.
- Do not mix metrics into one aggregate score.
- Preserve observation masks so missing observations are not treated as
  negatives.

## Open Items

- Add registry files to the downloader or a companion dataloader repository.
- Implement model-ready dataset adapters.
- Add a small checkpoint-loading smoke test for the Hugging Face model.
- Decide whether the broader model should use the existing `WildFIRE-FM` name
  or a new name for the multi-hazard backbone.
- Add release-version tags on Hugging Face and GitHub once the next model
  version is created.
