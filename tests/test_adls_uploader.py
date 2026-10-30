"""Unit tests for ADLS helpers (no real Azure calls)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.load.adls_uploader import find_latest_extract_dir


def test_find_latest_extract_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    raw = tmp_path / "raw"
    base = raw / "market_daily"
    older = base / "extract_date=2026-01-01"
    newer = base / "extract_date=2026-10-29"
    older.mkdir(parents=True)
    newer.mkdir(parents=True)

    monkeypatch.setattr(
        "src.load.adls_uploader.load_settings",
        lambda: {"paths": {"raw_local": raw}, "adls": {"bronze_prefix": "bronze/market_daily"}},
    )

    assert find_latest_extract_dir().name == "extract_date=2026-10-29"


def test_find_latest_extract_dir_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    raw = tmp_path / "raw"
    raw.mkdir()
    monkeypatch.setattr(
        "src.load.adls_uploader.load_settings",
        lambda: {"paths": {"raw_local": raw}, "adls": {"bronze_prefix": "bronze/market_daily"}},
    )
    with pytest.raises(FileNotFoundError):
        find_latest_extract_dir()
