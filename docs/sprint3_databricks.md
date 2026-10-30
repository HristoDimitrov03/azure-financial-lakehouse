# Sprint 3 — Databricks Medallion (plain English)

## Order (do not skip)

| Step | What |
|------|------|
| **H** | Create + launch Databricks workspace |
| **I** | Import notebooks `00`–`03` into folder `lakehouse` |
| **J** | Connect **Serverless** (or small Single Node) |
| **K** | Access Connector + UC external location (Serverless cannot use account-key spark.conf) |
| **L** | Run **01 → 02 → 03** |

Full click path: **`docs/azure_setup.md` → Sprint 3**.

## What each layer does

1. **Bronze** — raw CSV from ADLS → Delta  
2. **Silver** — clean types, drop bad rows, dedupe  
3. **Gold** — 7-day / 30-day moving averages for the dashboard  
