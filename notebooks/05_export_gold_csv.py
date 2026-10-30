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
export_df = gold.select(
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
).orderBy("ticker", "trade_date")

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
