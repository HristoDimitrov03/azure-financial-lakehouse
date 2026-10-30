"""
Build Gold-style metrics JSON/CSV for the Next.js dashboard (Sprint 5).

Default source: latest local Sprint 1 extract under data/raw/market_daily/.
Optional: --csv path to a Gold CSV exported from Databricks (notebook 05).

Last sync on the dashboard uses (in order):
  1. data/export/pipeline_sync.json (written by Databricks notebook 03/05)
  2. --synced-at CLI override
  3. max extracted_at_utc from the source CSV
  4. sibling _manifest.json extracted_at_utc
  5. generated_at_utc (JSON build time) as last resort

Outputs (for Vercel static hosting):
  web/public/data/gold_metrics.json
  data/export/gold_metrics.csv
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RAW_COLUMNS = [
    "trade_date",
    "ticker",
    "open",
    "high",
    "low",
    "close",
    "adj_close",
    "volume",
    "source",
    "extracted_at_utc",
]


def _latest_local_csv() -> Path:
    root = ROOT / "data" / "raw" / "market_daily"
    matches = sorted(root.glob("extract_date=*/market_ohlcv.csv"))
    if not matches:
        raise FileNotFoundError(
            f"No local extract found under {root}. Run scripts/run_extract.py first, "
            "or pass --csv path/to/gold_or_ohlcv.csv"
        )
    return matches[-1]


def _compute_gold_from_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    needed = {"trade_date", "ticker", "close"}
    missing = needed - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing columns: {sorted(missing)}")

    out = df.copy()
    out["trade_date"] = pd.to_datetime(out["trade_date"]).dt.strftime("%Y-%m-%d")
    out["ticker"] = out["ticker"].astype(str).str.upper().str.strip()
    out["close"] = pd.to_numeric(out["close"], errors="coerce")
    out = out.dropna(subset=["close", "trade_date", "ticker"])
    out = out.sort_values(["ticker", "trade_date"])

    # If this already looks like Gold (has ma_7d), keep metrics and normalize.
    if {"ma_7d", "ma_30d"}.issubset(out.columns):
        gold = out.copy()
        gold["ma_7d"] = pd.to_numeric(gold["ma_7d"], errors="coerce")
        gold["ma_30d"] = pd.to_numeric(gold["ma_30d"], errors="coerce")
        if "daily_return_pct" not in gold.columns:
            gold["daily_return_pct"] = (
                gold.groupby("ticker")["close"].pct_change() * 100.0
            )
        else:
            gold["daily_return_pct"] = pd.to_numeric(
                gold["daily_return_pct"], errors="coerce"
            )
    else:
        for col in ("open", "high", "low", "adj_close", "volume"):
            if col in out.columns:
                out[col] = pd.to_numeric(out[col], errors="coerce")
        out["ma_7d"] = out.groupby("ticker")["close"].transform(
            lambda s: s.rolling(7, min_periods=1).mean()
        )
        out["ma_30d"] = out.groupby("ticker")["close"].transform(
            lambda s: s.rolling(30, min_periods=1).mean()
        )
        out["daily_return_pct"] = out.groupby("ticker")["close"].pct_change() * 100.0
        gold = out

    keep = [
        c
        for c in [
            "trade_date",
            "ticker",
            "open",
            "high",
            "low",
            "close",
            "adj_close",
            "volume",
            "ma_7d",
            "ma_30d",
            "daily_return_pct",
        ]
        if c in gold.columns
    ]
    gold = gold.loc[:, keep].copy()
    for col in ("ma_7d", "ma_30d", "daily_return_pct", "close", "open", "high", "low", "adj_close"):
        if col in gold.columns:
            gold[col] = gold[col].round(4)
    return gold.reset_index(drop=True)


def _normalize_utc(value: str) -> str | None:
    text = (value or "").strip()
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _resolve_pipeline_synced_at(
    *,
    src: Path,
    raw_df: pd.DataFrame,
    sync_json: Path | None,
    synced_at_cli: str | None,
) -> tuple[str | None, str]:
    """Return (iso_utc or None, source_label)."""
    if synced_at_cli:
        normalized = _normalize_utc(synced_at_cli)
        if normalized:
            return normalized, "cli"

    candidates = []
    if sync_json is not None:
        candidates.append(sync_json)
    candidates.append(ROOT / "data" / "export" / "pipeline_sync.json")

    for path in candidates:
        if path is None or not path.is_file():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue
        stamp = payload.get("pipeline_synced_at_utc") or payload.get(
            "gold_built_at_utc"
        )
        normalized = _normalize_utc(str(stamp)) if stamp else None
        if normalized:
            return normalized, f"pipeline_sync:{path.name}"

    if "extracted_at_utc" in raw_df.columns:
        series = pd.to_datetime(raw_df["extracted_at_utc"], utc=True, errors="coerce")
        if series.notna().any():
            stamp = series.max().strftime("%Y-%m-%dT%H:%M:%SZ")
            return stamp, "csv:extracted_at_utc"

    manifest = src.parent / "_manifest.json"
    if manifest.is_file():
        try:
            payload = json.loads(manifest.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            payload = {}
        normalized = _normalize_utc(str(payload.get("extracted_at_utc") or ""))
        if normalized:
            return normalized, "manifest:extracted_at_utc"

    return None, "none"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Gold export for Next.js / Vercel")
    parser.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="Optional OHLCV or Gold CSV (default: latest local extract)",
    )
    parser.add_argument(
        "--sync-json",
        type=Path,
        default=None,
        help="Optional pipeline_sync.json from Databricks (default: data/export/)",
    )
    parser.add_argument(
        "--synced-at",
        type=str,
        default=None,
        help="Optional ISO UTC override for Last sync (e.g. 2026-10-29T17:11:24Z)",
    )
    args = parser.parse_args()

    src = args.csv if args.csv else _latest_local_csv()
    src = src.resolve()
    print(f"Reading {src}")
    raw_df = pd.read_csv(src)
    gold = _compute_gold_from_ohlcv(raw_df)

    export_dir = ROOT / "data" / "export"
    web_data = ROOT / "web" / "public" / "data"
    export_dir.mkdir(parents=True, exist_ok=True)
    web_data.mkdir(parents=True, exist_ok=True)

    csv_path = export_dir / "gold_metrics.csv"
    json_path = web_data / "gold_metrics.json"

    gold.to_csv(csv_path, index=False)

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    pipeline_synced_at, sync_source = _resolve_pipeline_synced_at(
        src=src,
        raw_df=raw_df,
        sync_json=args.sync_json.resolve() if args.sync_json else None,
        synced_at_cli=args.synced_at,
    )
    last_synced_at = pipeline_synced_at or generated_at

    payload = {
        "generated_at_utc": generated_at,
        "pipeline_synced_at_utc": pipeline_synced_at,
        "last_synced_at_utc": last_synced_at,
        "last_synced_source": sync_source if pipeline_synced_at else "generated_at_utc",
        "source_file": str(src.as_posix()),
        "row_count": int(len(gold)),
        "tickers": sorted(gold["ticker"].unique().tolist()),
        "date_min": str(gold["trade_date"].min()),
        "date_max": str(gold["trade_date"].max()),
        "rows": json.loads(gold.to_json(orient="records")),
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Wrote {csv_path} ({len(gold)} rows)")
    print(f"Wrote {json_path}")
    print(f"Tickers: {', '.join(payload['tickers'])}")
    print(f"Range: {payload['date_min']} → {payload['date_max']}")
    print(f"Last sync: {last_synced_at} (source={payload['last_synced_source']})")


if __name__ == "__main__":
    main()
