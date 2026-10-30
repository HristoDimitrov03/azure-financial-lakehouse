# Pipeline outline — `pl_daily_medallion`

Create this in **ADF Studio** (Sprint 4 Step P). After it works, optionally export JSON here.

```text
pl_daily_medallion
└── Databricks Job activity
      linkedService: ls_databricks
      job:           job_medallion_market
```

Databricks Job graph (created in Databricks UI, Step O):

```text
job_medallion_market
├── extract → notebook 04_daily_extract_to_adls  (Serverless, yfinance → ADLS)
├── bronze  → notebook 01_bronze_ingestion       (depends on extract)
├── silver  → notebook 02_silver_cleansing       (depends on bronze)
└── gold    → notebook 03_gold_metrics           (depends on silver)
```

Fallback if Job activity is unavailable: four ADF **Notebook** activities chained in the same order.
