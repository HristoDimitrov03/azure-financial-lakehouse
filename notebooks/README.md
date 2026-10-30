# Databricks notebooks

## Files

```text
00_config_and_auth.py      ← auth + paths (%run from others)
01_bronze_ingestion.py
02_silver_cleansing.py
03_gold_metrics.py
04_daily_extract_to_adls.py ← yfinance → ADLS landing (daily Job first task)
```

## Sprint 3 (manual)

Import `00`–`03` → UC external location → Run `01`→`02`→`03`.  
See `docs/azure_setup.md` Sprint 3.

## Sprint 4 (scheduled Job)

Import **`04`** into the same `lakehouse` folder.  
Databricks Job order:

`04 extract → 01 bronze → 02 silver → 03 gold`

ADF daily trigger starts that Job — fresh market data without your PC.
