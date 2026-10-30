# Azure Data Factory (Sprint 4)

ADF is the **orchestrator**: it starts a Databricks Job that runs Bronze → Silver → Gold.

## Target resources (Free Trial)

| Resource | Name |
|----------|------|
| Data Factory | `adf-financial-lakehouse` |
| Linked service | `ls_databricks` |
| Pipeline | `pl_daily_medallion` |
| Databricks Job | `job_medallion_market` |
| Schedule (optional) | `tr_daily_medallion` |

Click-by-click: **`docs/azure_setup.md` → Sprint 4** · Plain English: **`docs/sprint4_adf.md`**.

## Folders (export from portal after it works)

- `linked_services/` — e.g. `ls_databricks.json`
- `pipelines/` — e.g. `pl_daily_medallion.json`
- `datasets/` — unused in this sprint (no Copy activity yet)

## Scope note

The Databricks Job should run **`04` extract → Medallion** so the daily ADF schedule pulls live yfinance data.  
Local `scripts/run_extract.py` / `run_upload.py` remain optional for debugging.
