#!/usr/bin/env python3

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent / "downloader" / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from verify_download_scripts import main  # type: ignore


if __name__ == "__main__":
    raise SystemExit(main())
