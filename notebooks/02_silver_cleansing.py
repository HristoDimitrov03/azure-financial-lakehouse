# Databricks notebook source
# MAGIC %md
# MAGIC # 02 — Silver cleansing
# MAGIC **Goal:** Turn Bronze into trustworthy typed data:
# MAGIC - cast types
# MAGIC - drop unusable rows
# MAGIC - deduplicate on (`ticker`, `trade_date`)
# MAGIC
# MAGIC **Prerequisite:** `00_config_and_auth` + `01_bronze_ingestion`.

# COMMAND ----------

# MAGIC %run ./00_config_and_auth

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

bronze = spark.read.format("delta").load(BRONZE_DELTA)

silver = (
    bronze.select(
        F.to_date(F.col("trade_date")).alias("trade_date"),
        F.upper(F.trim(F.col("ticker"))).alias("ticker"),
        F.col("open").cast("double").alias("open"),
        F.col("high").cast("double").alias("high"),
        F.col("low").cast("double").alias("low"),
        F.col("close").cast("double").alias("close"),
        F.col("adj_close").cast("double").alias("adj_close"),
        F.col("volume").cast("long").alias("volume"),
        F.col("source").cast("string").alias("source"),
        F.to_timestamp(F.col("extracted_at_utc")).alias("extracted_at_utc"),
        F.col("_ingested_at_utc"),
        F.col("_source_system"),
    )
    # Business rules: must have a date, ticker, and close price
    .filter(F.col("trade_date").isNotNull())
    .filter(F.col("ticker").isNotNull() & (F.length(F.col("ticker")) > 0))
    .filter(F.col("close").isNotNull() & (F.col("close") > 0))
)

# If adj_close missing, fall back to close
silver = silver.withColumn(
    "adj_close",
    F.when(F.col("adj_close").isNull(), F.col("close")).otherwise(F.col("adj_close")),
)

# Deduplicate: keep newest extract for each ticker + trade_date
window = Window.partitionBy("ticker", "trade_date").orderBy(
    F.col("extracted_at_utc").desc_nulls_last(),
    F.col("_ingested_at_utc").desc_nulls_last(),
)
silver = (
    silver.withColumn("_row_rank", F.row_number().over(window))
    .filter(F.col("_row_rank") == 1)
    .drop("_row_rank")
)

print(f"Silver row count: {silver.count()}")
display(silver.limit(10))

# COMMAND ----------

(
    silver.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .save(SILVER_DELTA)
)

spark.sql(
    f"""
    CREATE TABLE IF NOT EXISTS {SILVER_TABLE}
    USING DELTA
    LOCATION '{SILVER_DELTA}'
    """
)

print(f"Wrote Silver Delta → {SILVER_DELTA}")
display(spark.table(SILVER_TABLE).limit(5))
