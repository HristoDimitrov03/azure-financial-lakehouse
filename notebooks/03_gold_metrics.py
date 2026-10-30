# Databricks notebook source
# MAGIC %md
# MAGIC # 03 — Gold metrics
# MAGIC **Goal:** Business-ready features for the Streamlit dashboard:
# MAGIC - 7-day moving average of `close`
# MAGIC - 30-day moving average of `close`
# MAGIC - simple daily return
# MAGIC
# MAGIC **Prerequisite:** `00_config_and_auth` + `02_silver_cleansing`.

# COMMAND ----------

# MAGIC %run ./00_config_and_auth

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

silver = spark.read.format("delta").load(SILVER_DELTA)

# Moving averages are calculated per ticker, ordered by trade date (trading days).
w = Window.partitionBy("ticker").orderBy("trade_date")

gold = (
    silver.select(
        "trade_date",
        "ticker",
        "open",
        "high",
        "low",
        "close",
        "adj_close",
        "volume",
    )
    .withColumn("ma_7d", F.avg("close").over(w.rowsBetween(-6, 0)))
    .withColumn("ma_30d", F.avg("close").over(w.rowsBetween(-29, 0)))
    .withColumn(
        "daily_return_pct",
        F.round(
            (F.col("close") - F.lag("close").over(w)) / F.lag("close").over(w) * 100.0,
            4,
        ),
    )
    .withColumn("_gold_built_at_utc", F.current_timestamp())
)

print(f"Gold row count: {gold.count()}")
display(gold.orderBy(F.col("trade_date").desc()).limit(20))

# COMMAND ----------

(
    gold.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .save(GOLD_DELTA)
)

spark.sql(
    f"""
    CREATE TABLE IF NOT EXISTS {GOLD_TABLE}
    USING DELTA
    LOCATION '{GOLD_DELTA}'
    """
)

print(f"Wrote Gold Delta → {GOLD_DELTA}")
print(f"Table: {GOLD_TABLE}")
display(spark.table(GOLD_TABLE).orderBy(F.col("trade_date").desc()).limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Sanity check — one ticker
# MAGIC Confirm moving averages look reasonable (smooth vs raw close).

# COMMAND ----------

sample_ticker = gold.select("ticker").limit(1).collect()[0][0]
display(
    gold.filter(F.col("ticker") == sample_ticker)
    .orderBy(F.col("trade_date").desc())
    .select("trade_date", "ticker", "close", "ma_7d", "ma_30d", "daily_return_pct")
    .limit(15)
)
