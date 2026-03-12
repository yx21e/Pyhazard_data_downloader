from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class DatasetSpec:
    name: str
    script: str
    time_mode: str = "none"  # none | range | year | recent_window
    aoi_mode: str = "unsupported"  # unsupported | native | postfilter
    notes: str = ""


DATASETS: Dict[str, DatasetSpec] = {
    "canopy_cover": DatasetSpec(
        "canopy_cover",
        "canopy_cover.py",
        notes="Static LANDFIRE canopy cover download.",
    ),
    "current_perimeters": DatasetSpec(
        "current_perimeters",
        "current_perimeters.py",
        notes="Current WFIGS perimeter snapshot.",
    ),
    "goes_geocolor": DatasetSpec(
        "goes_geocolor",
        "goes_geocolor.py",
        time_mode="range",
        notes="GOES GeoColor source files by date/hour.",
    ),
    "historical_fires": DatasetSpec(
        "historical_fires",
        "historical_fires.py",
        time_mode="range",
        notes="Historical fire datasets by date range.",
    ),
    "hpwren_real_time_weather_stations": DatasetSpec(
        "hpwren_real_time_weather_stations",
        "hpwren_real_time_weather_stations.py",
        time_mode="recent_window",
        notes="Recent HPWREN metadata and recent sample window.",
    ),
    "nasa_gibs": DatasetSpec(
        "nasa_gibs",
        "nasa_gibs.py",
        time_mode="range",
        notes="Global imagery by date and layer.",
    ),
    "nohrsc_snow_analysis": DatasetSpec(
        "nohrsc_snow_analysis",
        "nohrsc_snow_analysis.py",
        time_mode="range",
        notes="Daily SNODAS archive download.",
    ),
    "satellite_fire_detections_goes": DatasetSpec(
        "satellite_fire_detections_goes",
        "satellite_fire_detections_goes.py",
        time_mode="range",
        notes="GOES FDCF by date range.",
    ),
    "satellite_fire_detections_modis": DatasetSpec(
        "satellite_fire_detections_modis",
        "satellite_fire_detections_modis.py",
        time_mode="range",
        aoi_mode="native",
        notes="FIRMS MODIS CSV by date range and bounding box.",
    ),
    "satellite_fire_detections_viirs": DatasetSpec(
        "satellite_fire_detections_viirs",
        "satellite_fire_detections_viirs.py",
        time_mode="range",
        aoi_mode="native",
        notes="FIRMS VIIRS CSV by date range and bounding box.",
    ),
    "smoke_analysis": DatasetSpec(
        "smoke_analysis",
        "smoke_analysis.py",
        time_mode="year",
        notes="Annual smoke bundle by year.",
    ),
    "spot_forecast": DatasetSpec(
        "spot_forecast",
        "spot_forecast.py",
        notes="Current/recent spot forecast products.",
    ),
    "surface_fuels": DatasetSpec(
        "surface_fuels",
        "surface_fuels.py",
        notes="Static LANDFIRE surface fuels download.",
    ),
    "vegetation_type": DatasetSpec(
        "vegetation_type",
        "vegetation_type.py",
        notes="Static LANDFIRE vegetation type download.",
    ),
    "watches_and_warnings": DatasetSpec(
        "watches_and_warnings",
        "watches_and_warnings.py",
        time_mode="range",
        notes="NDFD warnings by date range.",
    ),
    "weather_forecast": DatasetSpec(
        "weather_forecast",
        "weather_forecast.py",
        time_mode="range",
        notes="NDFD and HRRR forecast downloads by date range.",
    ),
    "wrc_housing_density": DatasetSpec(
        "wrc_housing_density",
        "wrc_housing_density.py",
        notes="Static housing density raster download.",
    ),
}
