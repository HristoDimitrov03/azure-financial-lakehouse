# Sprint 4 — Azure Data Factory (plain English)

## What you build

A **daily orchestrator**: Azure Data Factory starts a **Databricks Job** that runs

`04 Extract → 01 Bronze → 02 Silver → 03 Gold`

on **Serverless**. Extract pulls **live yfinance** data into ADLS; Medallion rebuilds the lake.

| Piece | Role |
|-------|------|
| **04 notebook** | yfinance → ADLS `bronze/market_daily/...` |
| **01–03 notebooks** | Bronze → Silver → Gold |
| **Databricks Job** | Runs 04→01→02→03 in order |
| **ADF pipeline + schedule** | Starts that Job daily |

## Order (do not skip)

| Step | What |
|------|------|
| **M** | Create Azure Data Factory |
| **N** | Databricks token + ADF linked service |
| **O** | Databricks Job: `04 → 01 → 02 → 03` |
| **P** | ADF pipeline with Databricks **Job** activity |
| **Q** | Trigger now + daily schedule |

Full click path: **`docs/azure_setup.md` → Sprint 4**.

## Why extract started local, then moved to cloud

Sprint 1–2 used your PC to learn extract/upload. That made ADF “recompute old files” until we added **`04_daily_extract_to_adls`**.  
With **04** first in the Job, the daily schedule is a **real** market refresh — not only a toolkit demo.

Local `run_extract.py` / `run_upload.py` remain useful for debugging. Forever-free path after Azure teardown can still use **GitHub Actions**.

## Success looks like

- ADF pipeline run **Succeeded**  
- Databricks Job: all **four** tasks green (`extract`→`bronze`→`silver`→`gold`)  
- New `extract_date=YYYY-MM-DD` folder in ADLS  
- Gold has rows / `ma_7d` / `ma_30d`
