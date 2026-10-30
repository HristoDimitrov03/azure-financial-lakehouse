"""
Pull daily OHLCV bars from Yahoo Finance via yfinance and normalize to RAW schema.

Designed for local dry-runs in Sprint 1; Sprint 2 will upload the same CSV layout
to ADLS Gen2 under the bronze prefix.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd
import yfinance as yf

from src.extract.schema import RAW_OHLCV_COLUMNS
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

SOURCE_NAME = "yfinance"


@dataclass(frozen=True)
class ExtractResult:
    """Summary of one extract run (useful for logs and a small manifest)."""

    extract_date: str
    output_csv: Path
    tickers_requested: list[str]
    tickers_succeeded: list[str]
    tickers_failed: list[str]
    row_count: int


def _normalize_history(
    hist: pd.DataFrame,
    ticker: str,
    extracted_at_utc: str,
) -> pd.DataFrame:
    """
    Map a yfinance history DataFrame into the RAW_OHLCV_COLUMNS contract.

    yfinance column names vary slightly by version (Adj Close vs adjclose).
    We accept common variants and fail clearly if Close is missing.
    """
    if hist is None or hist.empty:
        return pd.DataFrame(columns=RAW_OHLCV_COLUMNS)

    df = hist.copy()
    # Flatten MultiIndex columns if present (happens with some download() shapes)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [str(c[-1]).strip() if isinstance(c, tuple) else str(c) for c in df.columns]

    colmap = {str(c).strip().lower().replace(" ", "_"): c for c in df.columns}

    def pick(*candidates: str) -> pd.Series | None:
        for name in candidates:
            key = name.lower().replace(" ", "_")
            if key in colmap:
                return df[colmap[key]]
        return None

    close = pick("close")
    if close is None:
        raise ValueError(f"{ticker}: history missing Close column; got {list(df.columns)}")

    adj = pick("adj_close", "adjclose", "adjusted_close")
    if adj is None:
        adj = close

    open_ = pick("open")
    high = pick("high")
    low = pick("low")
    volume = pick("volume")

    # Build with positional values only — avoids pandas aligning a RangeIndex
    # Series against a DatetimeIndex (which produced NaN trade_date).
    idx = pd.to_datetime(df.index)
    if getattr(idx, "tz", None) is not None:
        idx = idx.tz_convert("UTC").tz_localize(None)
    n = len(df)

    def as_float(series: pd.Series | None) -> list[float | None]:
        if series is None:
            return [None] * n
        return pd.to_numeric(series, errors="coerce").to_numpy().tolist()

    def as_int(series: pd.Series | None) -> list[int | None]:
        if series is None:
            return [None] * n
        values = pd.to_numeric(series, errors="coerce")
        # Keep nullable ints for CSV clarity
        return [None if pd.isna(v) else int(v) for v in values.to_numpy()]

    out = pd.DataFrame(
        {
            "trade_date": idx.strftime("%Y-%m-%d").tolist(),
            "ticker": [ticker.upper()] * n,
            "open": as_float(open_),
            "high": as_float(high),
            "low": as_float(low),
            "close": as_float(close),
            "adj_close": as_float(adj),
            "volume": as_int(volume),
            "source": [SOURCE_NAME] * n,
            "extracted_at_utc": [extracted_at_utc] * n,
        }
    )
    out["volume"] = pd.Series(out["volume"], dtype="Int64")
    out = out.dropna(subset=["close"]).reset_index(drop=True)
    return out.loc[:, RAW_OHLCV_COLUMNS]


def fetch_ticker_history(
    ticker: str,
    *,
    period: str = "1y",
    interval: str = "1d",
    extracted_at_utc: str | None = None,
) -> pd.DataFrame:
    """Download one ticker and return a normalized RAW-schema DataFrame."""
    extracted_at_utc = extracted_at_utc or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    logger.info("Fetching %s (period=%s, interval=%s)", ticker, period, interval)

    # auto_adjust=False keeps a separate adjusted close when available
    hist = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=False)
    return _normalize_history(hist, ticker, extracted_at_utc)


def extract_market_ohlcv(
    tickers: Iterable[str],
    *,
    period: str = "1y",
    interval: str = "1d",
    raw_root: Path,
    extract_date: str | None = None,
) -> ExtractResult:
    """
    Extract all tickers and write a single partitioned CSV under raw_root.

    Layout (Hive-style partition folder — Bronze-friendly):
      {raw_root}/market_daily/extract_date=YYYY-MM-DD/market_ohlcv.csv
      {raw_root}/market_daily/extract_date=YYYY-MM-DD/_manifest.json
    """
    extract_date = extract_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    extracted_at_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    tickers_list = [t.strip().upper() for t in tickers if str(t).strip()]

    frames: list[pd.DataFrame] = []
    succeeded: list[str] = []
    failed: list[str] = []

    for ticker in tickers_list:
        try:
            frame = fetch_ticker_history(
                ticker,
                period=period,
                interval=interval,
                extracted_at_utc=extracted_at_utc,
            )
            if frame.empty:
                logger.warning("%s returned 0 rows — marking as failed", ticker)
                failed.append(ticker)
                continue
            frames.append(frame)
            succeeded.append(ticker)
            logger.info("%s → %s rows", ticker, len(frame))
        except Exception as exc:  # noqa: BLE001 — per-ticker isolation for batch extract
            logger.exception("Failed to extract %s: %s", ticker, exc)
            failed.append(ticker)

    out_dir = raw_root / "market_daily" / f"extract_date={extract_date}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / "market_ohlcv.csv"

    if frames:
        combined = pd.concat(frames, ignore_index=True)
        combined = combined.sort_values(["ticker", "trade_date"]).reset_index(drop=True)
        combined = combined.loc[:, RAW_OHLCV_COLUMNS]
    else:
        combined = pd.DataFrame(columns=RAW_OHLCV_COLUMNS)

    combined.to_csv(out_csv, index=False)
    logger.info("Wrote %s rows → %s", len(combined), out_csv)

    manifest = {
        "extract_date": extract_date,
        "extracted_at_utc": extracted_at_utc,
        "period": period,
        "interval": interval,
        "tickers_requested": tickers_list,
        "tickers_succeeded": succeeded,
        "tickers_failed": failed,
        "row_count": int(len(combined)),
        "output_csv": str(out_csv.as_posix()),
        "schema": RAW_OHLCV_COLUMNS,
    }
    manifest_path = out_dir / "_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    logger.info("Wrote manifest → %s", manifest_path)

    return ExtractResult(
        extract_date=extract_date,
        output_csv=out_csv,
        tickers_requested=tickers_list,
        tickers_succeeded=succeeded,
        tickers_failed=failed,
        row_count=len(combined),
    )
