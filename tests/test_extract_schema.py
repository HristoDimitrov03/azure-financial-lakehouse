"""Unit tests for RAW OHLCV normalization (no network)."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from src.extract.schema import RAW_OHLCV_COLUMNS
from src.extract.yfinance_extractor import _normalize_history


def test_normalize_history_maps_standard_columns():
    idx = pd.to_datetime(["2024-01-02", "2024-01-03"])
    hist = pd.DataFrame(
        {
            "Open": [100.0, 101.0],
            "High": [105.0, 106.0],
            "Low": [99.0, 100.0],
            "Close": [104.0, 105.0],
            "Adj Close": [104.0, 105.0],
            "Volume": [1_000_000, 1_100_000],
        },
        index=idx,
    )
    extracted_at = datetime(2024, 1, 4, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = _normalize_history(hist, "aapl", extracted_at)

    assert list(out.columns) == RAW_OHLCV_COLUMNS
    assert out["ticker"].tolist() == ["AAPL", "AAPL"]
    assert out["trade_date"].tolist() == ["2024-01-02", "2024-01-03"]
    assert out["source"].unique().tolist() == ["yfinance"]
    assert out["extracted_at_utc"].unique().tolist() == [extracted_at]
    assert out["adj_close"].tolist() == [104.0, 105.0]


def test_normalize_history_falls_back_adj_close_to_close():
    idx = pd.to_datetime(["2024-01-02"])
    hist = pd.DataFrame(
        {"Open": [10.0], "High": [11.0], "Low": [9.0], "Close": [10.5], "Volume": [100]},
        index=idx,
    )
    out = _normalize_history(hist, "MSFT", "2024-01-02T00:00:00Z")
    assert out.iloc[0]["adj_close"] == 10.5
    assert out.iloc[0]["trade_date"] == "2024-01-02"


def test_normalize_history_empty():
    out = _normalize_history(pd.DataFrame(), "X", "2024-01-02T00:00:00Z")
    assert out.empty
    assert list(out.columns) == RAW_OHLCV_COLUMNS
