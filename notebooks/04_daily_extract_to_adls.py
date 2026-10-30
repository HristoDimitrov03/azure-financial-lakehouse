# Databricks notebook source
# MAGIC %md
# MAGIC # 04 — Daily extract (yfinance → ADLS landing)
# MAGIC Pulls fresh daily OHLCV for the portfolio tickers and writes:
# MAGIC
# MAGIC `abfss://.../bronze/market_daily/extract_date=YYYY-MM-DD/market_ohlcv.csv`
# MAGIC
# MAGIC Put this **first** in `job_medallion_market` so the daily ADF schedule
# MAGIC actually refreshes market data (not only re-runs Medallion on old CSVs).

# COMMAND ----------

# MAGIC %pip install yfinance pandas --quiet

# COMMAND ----------

# MAGIC %run ./00_config_and_auth

# COMMAND ----------

import json
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

TICKERS = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "META",
    "NVDA",
    "JPM",
    "V",
    "SPY",
]
PERIOD = "1y"
INTERVAL = "1d"
SOURCE_NAME = "yfinance"
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

# COMMAND ----------

def _normalize_history(hist: pd.DataFrame, ticker: str, extracted_at_utc: str) -> pd.DataFrame:
    if hist is None or hist.empty:
        return pd.DataFrame(columns=RAW_COLUMNS)

    df = hist.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [
            str(c[-1]).strip() if isinstance(c, tuple) else str(c) for c in df.columns
        ]

    colmap = {str(c).strip().lower().replace(" ", "_"): c for c in df.columns}

    def pick(*candidates: str):
        for name in candidates:
            key = name.lower().replace(" ", "_")
            if key in colmap:
                return df[colmap[key]]
        return None

    close = pick("close")
    if close is None:
        raise ValueError(f"{ticker}: missing Close; columns={list(df.columns)}")

    adj = pick("adj_close", "adjclose", "adjusted_close")
    if adj is None:
        adj = close

    open_ = pick("open")
    high = pick("high")
    low = pick("low")
    volume = pick("volume")

    idx = pd.to_datetime(df.index)
    if getattr(idx, "tz", None) is not None:
        idx = idx.tz_convert("UTC").tz_localize(None)
    n = len(df)

    def as_float(series):
        if series is None:
            return [None] * n
        return pd.to_numeric(series, errors="coerce").to_numpy().tolist()

    def as_int(series):
        if series is None:
            return [None] * n
        values = pd.to_numeric(series, errors="coerce")
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
    out = out.dropna(subset=["close"]).reset_index(drop=True)
    return out.loc[:, RAW_COLUMNS]


def fetch_all(tickers: list[str]) -> tuple[pd.DataFrame, list[str], list[str], str]:
    extracted_at_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    frames: list[pd.DataFrame] = []
    succeeded: list[str] = []
    failed: list[str] = []

    for ticker in tickers:
        try:
            hist = yf.Ticker(ticker).history(
                period=PERIOD, interval=INTERVAL, auto_adjust=False
            )
            frame = _normalize_history(hist, ticker, extracted_at_utc)
            if frame.empty:
                failed.append(ticker)
                print(f"{ticker}: 0 rows")
                continue
            frames.append(frame)
            succeeded.append(ticker)
            print(f"{ticker}: {len(frame)} rows")
        except Exception as exc:  # noqa: BLE001
            failed.append(ticker)
            print(f"{ticker}: FAILED — {exc}")

    if frames:
        combined = pd.concat(frames, ignore_index=True)
        combined = combined.sort_values(["ticker", "trade_date"]).reset_index(drop=True)
    else:
        combined = pd.DataFrame(columns=RAW_COLUMNS)

    return combined, succeeded, failed, extracted_at_utc

# COMMAND ----------

extract_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
combined, succeeded, failed, extracted_at_utc = fetch_all(TICKERS)

assert not combined.empty, "Extract returned 0 rows — check yfinance / network on Serverless."
assert succeeded, "No tickers succeeded."

print(f"extract_date={extract_date} rows={len(combined)} ok={succeeded} failed={failed}")
display(spark.createDataFrame(combined.head(20).astype(str)))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write landing CSV + manifest to ADLS

# COMMAND ----------

target_dir = f"{RAW_CSV_ROOT}/extract_date={extract_date}"
target_csv = f"{target_dir}/market_ohlcv.csv"
target_manifest = f"{target_dir}/_manifest.json"

# Serverless blocks dbutils.fs.cp from file:/tmp — write CSV text straight to ADLS.
dbutils.fs.mkdirs(target_dir)
dbutils.fs.put(target_csv, combined.to_csv(index=False), overwrite=True)

manifest = {
    "extract_date": extract_date,
    "extracted_at_utc": extracted_at_utc,
    "period": PERIOD,
    "interval": INTERVAL,
    "tickers_requested": TICKERS,
    "tickers_succeeded": succeeded,
    "tickers_failed": failed,
    "row_count": int(len(combined)),
    "output_csv": target_csv,
    "schema": RAW_COLUMNS,
    "runner": "databricks_notebook_04",
}
dbutils.fs.put(target_manifest, json.dumps(manifest, indent=2), overwrite=True)

print(f"Wrote {target_csv}")
print(f"Wrote {target_manifest}")
display(dbutils.fs.ls(target_dir))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Pipeline sync stamp — scrape time for the web dashboard

# COMMAND ----------

SYNC_PATH = f"{base_abfss}/export/pipeline_sync.json"
pipeline_sync = {
    "extracted_at_utc": extracted_at_utc,
    "pipeline_synced_at_utc": extracted_at_utc,
    "source": "databricks_notebook_04",
    "extract_date": extract_date,
    "output_csv": target_csv,
}
dbutils.fs.mkdirs(f"{base_abfss}/export")
dbutils.fs.put(SYNC_PATH, json.dumps(pipeline_sync, indent=2), overwrite=True)
print(f"Wrote pipeline sync stamp → {SYNC_PATH}")
print(json.dumps(pipeline_sync, indent=2))
