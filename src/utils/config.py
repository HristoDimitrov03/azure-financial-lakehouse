"""
Load project YAML config (tickers + settings) from the repo root.

Paths in YAML are relative to the project root so scripts work no matter
which working directory you launch them from.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def get_project_root() -> Path:
    """Return the repository root (folder that contains config/, src/, data/)."""
    # src/utils/config.py → parents[0]=utils, [1]=src, [2]=repo root
    return Path(__file__).resolve().parents[2]


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}, got {type(data).__name__}")
    return data


def load_tickers_config(path: Path | None = None) -> dict[str, Any]:
    """Load config/tickers.yaml (ticker list + history window)."""
    cfg_path = path or (get_project_root() / "config" / "tickers.yaml")
    cfg = _load_yaml(cfg_path)
    tickers = cfg.get("tickers") or []
    if not tickers:
        raise ValueError(f"No tickers defined in {cfg_path}")
    # Strip inline comments leftovers if YAML ever stores "AAPL    # Apple" as string — usually fine
    cleaned = [str(t).split("#")[0].strip().upper() for t in tickers]
    cleaned = [t for t in cleaned if t]
    cfg["tickers"] = cleaned
    history = cfg.setdefault("history", {})
    history.setdefault("period", "1y")
    history.setdefault("interval", "1d")
    return cfg


def load_settings(path: Path | None = None) -> dict[str, Any]:
    """
    Load settings.yaml, falling back to settings.example.yaml.

    Resolves path strings under `paths` to absolute Paths under the project root.
    """
    root = get_project_root()
    if path is None:
        primary = root / "config" / "settings.yaml"
        fallback = root / "config" / "settings.example.yaml"
        cfg_path = primary if primary.exists() else fallback
    else:
        cfg_path = path

    cfg = _load_yaml(cfg_path)
    paths = cfg.setdefault("paths", {})
    for key, default in (
        ("raw_local", "data/raw"),
        ("processed_local", "data/processed"),
        ("export_local", "data/export"),
    ):
        rel = paths.get(key, default)
        paths[key] = (root / rel).resolve()

    logger.debug("Loaded settings from %s", cfg_path)
    return cfg
