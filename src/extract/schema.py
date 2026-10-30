"""
Bronze / raw-layer schema contract for daily OHLCV extracts.

Every CSV written by the extractor MUST match RAW_OHLCV_COLUMNS in this order.
Downstream Databricks Bronze notebooks will rely on these names.
"""

from __future__ import annotations

from typing import Final

# Canonical column order for data/raw/.../market_ohlcv.csv
RAW_OHLCV_COLUMNS: Final[list[str]] = [
    "trade_date",  # calendar date of the bar (YYYY-MM-DD), timezone-naive date
    "ticker",  # uppercase symbol, e.g. AAPL
    "open",
    "high",
    "low",
    "close",
    "adj_close",  # adjusted close when yfinance provides it; else equals close
    "volume",
    "source",  # always "yfinance" for this pipeline
    "extracted_at_utc",  # ISO-8601 UTC timestamp of this extract run
]

# Light dtype expectations (pandas / Spark can refine in Silver)
RAW_OHLCV_DTYPES: Final[dict[str, str]] = {
    "trade_date": "string",  # stored as date string in CSV; cast in Silver
    "ticker": "string",
    "open": "float64",
    "high": "float64",
    "low": "float64",
    "close": "float64",
    "adj_close": "float64",
    "volume": "Int64",  # pandas nullable int
    "source": "string",
    "extracted_at_utc": "string",
}
