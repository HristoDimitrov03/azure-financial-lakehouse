# Databricks notebook source
# MAGIC %md
# MAGIC # 05 — Export Gold CSV for the web app
# MAGIC Writes a flat CSV the Next.js / Vercel app can download:
# MAGIC
# MAGIC `abfss://.../export/gold_metrics.csv`
# MAGIC
# MAGIC Then on your PC:
# MAGIC ```text
# MAGIC python scripts/download_gold_export.py
# MAGIC python scripts/build_gold_export.py --csv data/export/gold_metrics.csv
# MAGIC ```

# COMMAND ----------

# MAGIC %run ./00_config_and_auth

# COMMAND ----------

from pyspark.sql import functions as F

EXPORT_CSV = f"{base_abfss}/export/gold_metrics.csv"

gold = spark.read.format("delta").load(GOLD_DELTA)
cols = [
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
if "extracted_at_utc" in gold.columns:
    cols.append("extracted_at_utc")

export_df = gold.select(*cols).orderBy("ticker", "trade_date")

print(f"Exporting {export_df.count()} rows → {EXPORT_CSV}")

(
    export_df.coalesce(1)
    .write.mode("overwrite")
    .option("header", True)
    .csv(f"{base_abfss}/export/_gold_tmp")
)

files = [
    f.path
    for f in dbutils.fs.ls(f"{base_abfss}/export/_gold_tmp")
    if f.name.startswith("part-") and f.name.endswith(".csv")
]
assert files, "Spark CSV write produced no part file"
dbutils.fs.rm(EXPORT_CSV, True)
dbutils.fs.cp(files[0], EXPORT_CSV)
dbutils.fs.rm(f"{base_abfss}/export/_gold_tmp", True)

print(f"Wrote {EXPORT_CSV}")
display(export_df.orderBy(F.col("trade_date").desc()).limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Refresh pipeline sync stamp
# MAGIC **Last sync** = scrape time (`extracted_at_utc`), not export/Gold build time.

# COMMAND ----------

import json
from datetime import datetime, timezone

SYNC_PATH = f"{base_abfss}/export/pipeline_sync.json"


def _fmt_ts(value):
    if value is None:
        return None
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")
    text = str(value).replace(" ", "T")
    if text.endswith("+00:00"):
        text = text[:-6] + "Z"
    return text


extracted_at = None
if "extracted_at_utc" in gold.columns:
    row = gold.agg(F.max("extracted_at_utc").alias("ts")).collect()[0]
    extracted_at = _fmt_ts(row["ts"])

built = None
if "_gold_built_at_utc" in gold.columns:
    row = gold.agg(F.max("_gold_built_at_utc").alias("ts")).collect()[0]
    built = _fmt_ts(row["ts"])

synced_at = extracted_at or built or datetime.now(timezone.utc).strftime(
    "%Y-%m-%dT%H:%M:%SZ"
)
pipeline_sync = {
    "extracted_at_utc": extracted_at,
    "pipeline_synced_at_utc": synced_at,
    "gold_built_at_utc": built,
    "source": "databricks_05_export",
    "export_csv": EXPORT_CSV,
}
dbutils.fs.mkdirs(f"{base_abfss}/export")
dbutils.fs.put(SYNC_PATH, json.dumps(pipeline_sync, indent=2), overwrite=True)
print(f"Wrote pipeline sync stamp → {SYNC_PATH}")
print(json.dumps(pipeline_sync, indent=2))
