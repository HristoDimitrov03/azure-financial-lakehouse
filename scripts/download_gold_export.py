"""
Download Gold CSV + scrape-time stamps from ADLS to data/export/.

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


def _download_latest_extract_manifest(fs, local: Path) -> bool:
    try:
        mans = [
            p.name
            for p in fs.get_paths(path="bronze/market_daily", recursive=True)
            if p.name.endswith("_manifest.json")
        ]
    except Exception as exc:  # noqa: BLE001
        print(f"Skip extract manifest listing: {exc}")
        return False
    if not mans:
        print("Skip extract manifest: none under bronze/market_daily")
        return False
    remote = sorted(mans)[-1]
    return _download(fs, remote, local)


def main() -> None:
    load_dotenv(ROOT / ".env", override=False)
    container = (os.getenv("AZURE_STORAGE_CONTAINER") or "market-data").strip()
    export_dir = ROOT / "data" / "export"
    export_dir.mkdir(parents=True, exist_ok=True)

    client, account = get_datalake_service_client()
    fs = client.get_file_system_client(container)
    print(f"Downloading from abfss://{container}@{account}/...")

    ok_csv = _download(fs, "export/gold_metrics.csv", export_dir / "gold_metrics.csv")
    ok_sync = _download(
        fs, "export/pipeline_sync.json", export_dir / "pipeline_sync.json"
    )
    ok_manifest = _download_latest_extract_manifest(
        fs, export_dir / "extract_manifest.json"
    )

    if not ok_csv:
        raise SystemExit(
            "gold_metrics.csv missing in ADLS. Run Databricks notebook 05 first."
        )
    if not ok_sync and not ok_manifest:
        print(
            "Note: no scrape stamp found yet. Re-import notebooks 04/03/05 so "
            "Last sync can use extracted_at_utc."
        )
    print("Next: python scripts/build_gold_export.py --csv data/export/gold_metrics.csv")


if __name__ == "__main__":
    main()
