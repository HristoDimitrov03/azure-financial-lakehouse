# Sprint 2 — Storage on Azure (Free Trial)

## What this sprint means

Sprint 1 saved market data on your PC.  
Sprint 2 copies that CSV into **ADLS Gen2** on your **Azure Free Trial** account.

## Split of work

| Who | What |
|-----|------|
| **You** | Portal: RG + storage + container; paste connection string into `.env` |
| **Code** | `scripts/run_upload.py` already uploads to `bronze/market_daily/...` |

Follow **`docs/azure_setup.md` → Sprint 2** (Free Trial restart).

## Important

Update `.env` to the **new** storage account. Old Students connection strings will fail or upload to the wrong account.
