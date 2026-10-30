"""
Upload local raw extract files to Azure Data Lake Storage Gen2.

Auth options (first match wins):
  1. AZURE_STORAGE_CONNECTION_STRING  — simplest for Sprint 2 learning
  2. Service principal via AZURE_TENANT_ID / AZURE_CLIENT_ID / AZURE_CLIENT_SECRET
     + AZURE_STORAGE_ACCOUNT_NAME (enterprise-style)

Container layout (matches local dry-run + Medallion naming):
  {container}/{bronze_prefix}/extract_date=YYYY-MM-DD/market_ohlcv.csv
  {container}/{bronze_prefix}/extract_date=YYYY-MM-DD/_manifest.json
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.identity import ClientSecretCredential
from azure.storage.filedatalake import DataLakeServiceClient
from dotenv import load_dotenv

from src.utils.config import get_project_root, load_settings
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class UploadResult:
    """Summary of files pushed to ADLS."""

    account_name: str
    container: str
    remote_paths: list[str]
    local_files: list[str]


def _load_env() -> None:
    """Load .env from repo root so scripts work from any cwd."""
    load_dotenv(get_project_root() / ".env", override=False)


def get_datalake_service_client() -> tuple[DataLakeServiceClient, str]:
    """
    Build a DataLakeServiceClient and return (client, account_name).

    Raises ValueError with a clear message if credentials are missing.
    """
    _load_env()

    conn = (os.getenv("AZURE_STORAGE_CONNECTION_STRING") or "").strip()
    if conn and "AccountName=" in conn:
        # Parse account name for logging / result metadata
        account_name = ""
        for part in conn.split(";"):
            if part.startswith("AccountName="):
                account_name = part.split("=", 1)[1]
                break
        client = DataLakeServiceClient.from_connection_string(conn)
        logger.info("ADLS auth: connection string (account=%s)", account_name or "?")
        return client, account_name or "unknown"

    account_name = (os.getenv("AZURE_STORAGE_ACCOUNT_NAME") or "").strip()
    tenant_id = (os.getenv("AZURE_TENANT_ID") or "").strip()
    client_id = (os.getenv("AZURE_CLIENT_ID") or "").strip()
    client_secret = (os.getenv("AZURE_CLIENT_SECRET") or "").strip()

    if not account_name:
        raise ValueError(
            "Missing Azure storage config. Set AZURE_STORAGE_CONNECTION_STRING "
            "or AZURE_STORAGE_ACCOUNT_NAME (+ service principal vars) in .env. "
            "See docs/azure_setup.md (Sprint 2)."
        )

    if not (tenant_id and client_id and client_secret) or tenant_id.startswith(
        "00000000"
    ) or client_secret in {"replace_me", ""}:
        raise ValueError(
            "Azure credentials not configured. Easiest path for Sprint 2:\n"
            "  1) Follow docs/azure_setup.md\n"
            "  2) Paste AZURE_STORAGE_CONNECTION_STRING into .env\n"
            "  (Optional later: service principal Tenant/Client/Secret.)"
        )

    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
    )
    account_url = f"https://{account_name}.dfs.core.windows.net"
    client = DataLakeServiceClient(account_url=account_url, credential=credential)
    logger.info("ADLS auth: service principal (account=%s)", account_name)
    return client, account_name


def _ensure_file_system(service: DataLakeServiceClient, container: str) -> None:
    """Create the container (file system) if the user has not created it yet."""
    try:
        service.create_file_system(file_system=container)
        logger.info("Created container (file system): %s", container)
    except ResourceExistsError:
        logger.debug("Container already exists: %s", container)


def _ensure_directory(file_system_client, directory_path: str) -> None:
    """Create directory path in the lake if it does not exist (idempotent)."""
    directory_client = file_system_client.get_directory_client(directory_path)
    try:
        directory_client.get_directory_properties()
    except ResourceNotFoundError:
        directory_client.create_directory()
        logger.debug("Created directory: %s", directory_path)


def upload_file(
    *,
    local_path: Path,
    remote_path: str,
    container: str | None = None,
) -> str:
    """
    Upload one local file to ADLS Gen2.

    remote_path is the path *inside* the container, e.g.
    bronze/market_daily/extract_date=2026-10-29/market_ohlcv.csv
    """
    local_path = Path(local_path)
    if not local_path.is_file():
        raise FileNotFoundError(f"Local file not found: {local_path}")

    _load_env()
    container = container or (os.getenv("AZURE_STORAGE_CONTAINER") or "market-data").strip()
    service, _account = get_datalake_service_client()
    _ensure_file_system(service, container)
    fs = service.get_file_system_client(container)

    # Ensure parent directory exists (ADLS hierarchical namespace)
    parent = str(Path(remote_path).parent).replace("\\", "/")
    if parent and parent not in {".", ""}:
        _ensure_directory(fs, parent)

    file_client = fs.get_file_client(remote_path)
    with local_path.open("rb") as fh:
        file_client.upload_data(fh, overwrite=True)

    logger.info("Uploaded %s → abfs://%s/%s", local_path.name, container, remote_path)
    return remote_path


def upload_extract_partition(
    extract_dir: Path,
    *,
    container: str | None = None,
    bronze_prefix: str | None = None,
) -> UploadResult:
    """
    Upload market_ohlcv.csv + _manifest.json from a local extract_date=... folder.

    extract_dir example:
      data/raw/market_daily/extract_date=2026-10-29
    """
    extract_dir = Path(extract_dir)
    if not extract_dir.is_dir():
        raise FileNotFoundError(f"Extract directory not found: {extract_dir}")

    settings = load_settings()
    bronze_prefix = bronze_prefix or settings["adls"]["bronze_prefix"]
    # Folder name should be extract_date=YYYY-MM-DD
    partition_folder = extract_dir.name
    if not partition_folder.startswith("extract_date="):
        raise ValueError(
            f"Expected folder named extract_date=YYYY-MM-DD, got: {partition_folder}"
        )

    _load_env()
    container = container or (os.getenv("AZURE_STORAGE_CONTAINER") or "market-data").strip()
    service, account_name = get_datalake_service_client()
    # Touch filesystem client early so auth errors fail fast
    _ = service.get_file_system_client(container)

    candidates = ["market_ohlcv.csv", "_manifest.json"]
    remote_paths: list[str] = []
    local_files: list[str] = []

    for name in candidates:
        local = extract_dir / name
        if not local.exists():
            logger.warning("Skipping missing file: %s", local)
            continue
        remote = f"{bronze_prefix}/{partition_folder}/{name}".replace("\\", "/")
        upload_file(local_path=local, remote_path=remote, container=container)
        remote_paths.append(remote)
        local_files.append(str(local))

    if not remote_paths:
        raise FileNotFoundError(f"No uploadable files in {extract_dir}")

    return UploadResult(
        account_name=account_name,
        container=container,
        remote_paths=remote_paths,
        local_files=local_files,
    )


def find_latest_extract_dir(raw_root: Path | None = None) -> Path:
    """Pick the newest data/raw/market_daily/extract_date=* folder."""
    settings = load_settings()
    raw_root = Path(raw_root or settings["paths"]["raw_local"])
    base = raw_root / "market_daily"
    if not base.exists():
        raise FileNotFoundError(
            f"No raw extracts under {base}. Run: python scripts/run_extract.py"
        )
    partitions = sorted(
        [p for p in base.iterdir() if p.is_dir() and p.name.startswith("extract_date=")],
        key=lambda p: p.name,
    )
    if not partitions:
        raise FileNotFoundError(f"No extract_date=* folders under {base}")
    return partitions[-1]
