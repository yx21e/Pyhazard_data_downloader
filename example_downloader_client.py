#!/usr/bin/env python3

from downloader import DownloadRequest, download_data, list_datasets, save_download_report


def main() -> None:
    print("available downloader datasets:")
    for row in list_datasets():
        print(f"- {row['name']}: time_mode={row['time_mode']}, aoi_mode={row['aoi_mode']}")

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
    for item in results:
        print(item["dataset"], item["status"], item["returncode"], item["warnings"])
    report = save_download_report(results, "/home/yangshuang/output/downloader_example/report.json")
    print("report saved:", report)


if __name__ == "__main__":
    main()
