"""
CLI — upload the latest (or specified) local extract partition to ADLS Gen2.

Prerequisites:
  1. Complete Azure portal steps in docs/azure_setup.md (Sprint 2)
  2. Put credentials in .env (connection string recommended for starters)
  3. Have a local extract: python scripts/run_extract.py

Usage:
  python scripts/run_upload.py
  python scripts/run_upload.py --extract-dir data/raw/market_daily/extract_date=2026-10-29
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.load.adls_uploader import find_latest_extract_dir, upload_extract_partition
from src.utils.logging_config import get_logger

logger = get_logger("run_upload")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Upload local raw market extract to Azure Data Lake Storage Gen2.",
    )
    parser.add_argument(
        "--extract-dir",
        default=None,
        help="Path to extract_date=YYYY-MM-DD folder. Default: newest under data/raw.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        extract_dir = (
            Path(args.extract_dir) if args.extract_dir else find_latest_extract_dir()
        )
        logger.info("Uploading partition: %s", extract_dir)
        result = upload_extract_partition(extract_dir)
    except Exception as exc:  # noqa: BLE001 — CLI surface clear errors
        logger.error("%s", exc)
        return 1

    logger.info(
        "Upload complete | account=%s | container=%s | files=%s",
        result.account_name,
        result.container,
        result.remote_paths,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
