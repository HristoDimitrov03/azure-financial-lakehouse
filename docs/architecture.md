# Architecture notes

## Medallion layers (simple)

| Layer | Question it answers | Typical content |
|-------|---------------------|-----------------|
| Bronze | What did we receive? | Raw CSV from yfinance, plus ingest metadata |
| Silver | Can we trust it? | Typed columns, nulls handled, duplicates removed |
| Gold | What should the business see? | Moving averages and dashboard-ready metrics |

## Why batch (once per day)?

End-of-day market analytics and reporting usually need a reliable daily snapshot,
not tick-by-tick streaming. That matches real junior DE / DA work and keeps cost low.

## Orchestration (Sprint 4)

Azure Data Factory does **not** transform data itself. It starts a Databricks Job:

`04 Extract (yfinance → ADLS) → 01 Bronze → 02 Silver → 03 Gold` (Serverless).

That daily path refreshes **live** market data in the lake without your PC.  
Local extract/upload remains a debug fallback. After Portfolio Pivot, GitHub Actions can replace Azure for forever-free refresh.

## Dashboard (Sprint 5)

Next.js app in `web/` reads `public/data/gold_metrics.json` (built by
`scripts/build_gold_export.py`). Host on **Vercel** with Root Directory = `web`.

## Portfolio Pivot

1. Prove the live Azure path (Loom) + Vercel dashboard.
2. Keep refreshing `gold_metrics.json` (script or GitHub Actions).
3. Delete Azure resource group when Free Trial demo is done.
4. Optional: GitHub Actions cron to rebuild the JSON without Azure.
