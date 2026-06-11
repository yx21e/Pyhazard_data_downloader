#!/usr/bin/env python3

from downloader import ProviderDownloadRequest, download_provider_data, list_provider_datasets


def main() -> None:
    print("available provider datasets:")
    for row in list_provider_datasets():
        print(f"- {row['name']}: access={row['access']}, time_mode={row['time_mode']}")

    request = ProviderDownloadRequest(
        datasets=["aqs_pm25", "hms_smoke", "ibtracs"],
        output_root="./downloads_demo",
        years=(2024, 2024),
        dry_run=True,
        max_files=2,
    )
    results = download_provider_data(request)
    for item in results:
        print(item["dataset"], item["status"], item.get("counts", {}))


if __name__ == "__main__":
    main()
