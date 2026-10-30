"""
Download Gold CSV + pipeline sync stamp from ADLS to data/export/.

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


def _download(fs, remote: str, local: Path) -> bool:
    file_client = fs.get_file_client(remote)
    try:
        download = file_client.download_file()
        data = download.readall()
    except Exception as exc:  # noqa: BLE001 — surface missing blob clearly
        print(f"Skip {remote}: {exc}")
        return False
    local.parent.mkdir(parents=True, exist_ok=True)
    local.write_bytes(data)
    print(f"Wrote {local} ({len(data)} bytes)")
    return True


def main() -> None:
    load_dotenv(ROOT / ".env", override=False)
    container = (os.getenv("AZURE_STORAGE_CONTAINER") or "market-data").strip()
    export_dir = ROOT / "data" / "export"
    export_dir.mkdir(parents=True, exist_ok=True)

    client, account = get_datalake_service_client()
    fs = client.get_file_system_client(container)
    print(f"Downloading from abfss://{container}@{account}/.../export/")

    ok_csv = _download(fs, "export/gold_metrics.csv", export_dir / "gold_metrics.csv")
    ok_sync = _download(
        fs, "export/pipeline_sync.json", export_dir / "pipeline_sync.json"
    )

    if not ok_csv:
        raise SystemExit(
            "gold_metrics.csv missing in ADLS. Run Databricks notebook 05 first."
        )
    if not ok_sync:
        print(
            "Note: pipeline_sync.json not found yet. Re-run notebook 03 (or 05) "
            "so Last sync can use the Medallion stamp."
        )
    print("Next: python scripts/build_gold_export.py --csv data/export/gold_metrics.csv")


if __name__ == "__main__":
    main()
