# Restart on Azure Free Trial — where to begin

## Keep (no redo)

- Sprint 0 repo / venv / Docker skeleton  
- Sprint 1 local extract (`python scripts/run_extract.py`)  
- Notebook source files in `notebooks/`  

## Redo on the new Free Trial account

1. **Sprint 2** — new RG, storage, container, `.env`, upload — **done** (`stfinlakehousehd`)  
2. **Sprint 3** — Databricks Medallion — **done**  
3. **Sprint 4** — Azure Data Factory orchestration — **done**  
4. **Sprint 5** — Next.js on Vercel + Loom — **now** (`docs/sprint5_vercel.md`)  

## Do not

- Reuse Students storage connection string in `.env`  
- Expect the old Students Databricks workspace to work with the new account  
- Leave clusters / ADF schedules running overnight when not demoing (unless you want daily refreshes on Free Trial)  

## Start now

```powershell
python scripts\build_gold_export.py
cd web
npm run dev
```
