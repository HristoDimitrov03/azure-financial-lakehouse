"""
Download Gold CSV from ADLS (written by Databricks notebook 05) to data/export/.

Requires .env with AZURE_STORAGE_CONNECTION_STRING (Sprint 2).

Usage:
  python scripts/download_gold_export.py
  python scripts/build_gold_export.py --csv data/export/gold_metrics.csv
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.load.adls_uploader import get_datalake_service_client  # noqa: E402


def main() -> None:
    load_dotenv(ROOT / ".env", override=False)
    container = (os.getenv("AZURE_STORAGE_CONTAINER") or "market-data").strip()
    remote = "export/gold_metrics.csv"
    local = ROOT / "data" / "export" / "gold_metrics.csv"
    local.parent.mkdir(parents=True, exist_ok=True)

    client, account = get_datalake_service_client()
    fs = client.get_file_system_client(container)
    file_client = fs.get_file_client(remote)

    print(f"Downloading abfss://{container}@{account}/.../{remote}")
    download = file_client.download_file()
    data = download.readall()
    local.write_bytes(data)
    print(f"Wrote {local} ({len(data)} bytes)")
    print("Next: python scripts/build_gold_export.py --csv data/export/gold_metrics.csv")


if __name__ == "__main__":
    main()
