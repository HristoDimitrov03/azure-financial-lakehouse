# Sprint 1 — Extraction (plain English)

## What we built

A Python job that downloads about one year of **daily** stock prices for the
tickers in `config/tickers.yaml`, cleans the column names into a fixed schema,
and saves one CSV plus a small JSON manifest under `data/raw/`.

## Why a fixed schema?

Bronze (next cloud steps) should not guess column names. Every extract run
writes the same headers so Databricks can ingest reliably.

## How to run

```powershell
.\.venv\Scripts\Activate.ps1
python scripts/run_extract.py
```

## Success looks like

- Log lines per ticker with row counts
- A CSV you can open in Excel
- `_manifest.json` listing succeeded/failed tickers

## Not in this sprint

Uploading to Azure, Databricks, or ADF — that starts in Sprint 2+.
