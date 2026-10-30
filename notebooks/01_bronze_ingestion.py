# Databricks notebook source
# MAGIC %md
# MAGIC # 01 — Bronze ingestion
# MAGIC **Goal:** Read raw `market_ohlcv.csv` files from ADLS (Sprint 2 upload) and write a
# MAGIC Bronze **Delta** table. Keep data close to source — light metadata only.
# MAGIC
# MAGIC **Prerequisite:** run `00_config_and_auth` on this cluster first (defines paths).

# COMMAND ----------

# MAGIC %run ./00_config_and_auth

# COMMAND ----------

from pyspark.sql import functions as F

# COMMAND ----------

# MAGIC %md
# MAGIC ## Read all extract partitions
# MAGIC Path pattern: `bronze/market_daily/extract_date=YYYY-MM-DD/market_ohlcv.csv`

# COMMAND ----------

# Read as strings first — Bronze preserves the landing schema; Silver casts types.
bronze_df = (
    spark.read.option("header", True)
    .option("inferSchema", False)
    .csv(f"{RAW_CSV_ROOT}/extract_date=*/market_ohlcv.csv")
    .withColumn("ticker", F.upper(F.trim(F.col("ticker"))))
    .withColumn("_ingested_at_utc", F.current_timestamp())
    .withColumn("_source_system", F.lit("yfinance_adls_landing"))
)

assert bronze_df.take(1), "Bronze read returned 0 rows — check upload path in ADLS."

print(f"Bronze row count: {bronze_df.count()}")
display(bronze_df.limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write Bronze Delta (+ register table)

# COMMAND ----------

(
    bronze_df.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .save(BRONZE_DELTA)
)

spark.sql(
    f"""
    CREATE TABLE IF NOT EXISTS {BRONZE_TABLE}
    USING DELTA
    LOCATION '{BRONZE_DELTA}'
    """
)

print(f"Wrote Bronze Delta → {BRONZE_DELTA}")
print(f"Table: {BRONZE_TABLE}")
display(spark.table(BRONZE_TABLE).limit(5))
