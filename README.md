# Azure Financial Market Data Lakehouse

> Portfolio flagship: Medallion Architecture on Azure → free forever Streamlit demo.

A daily **batch** pipeline that extracts stock market data, stores it in ADLS Gen2,
cleans and enriches it in Databricks (Bronze → Silver → Gold), orchestrates with
Azure Data Factory, and serves insights via Streamlit.

**Portfolio Pivot:** after proving the live cloud path (Loom demo), Gold data is
exported locally so the Dockerized app can host for free with zero Azure cost.

---

## Architecture (high level)

```text
yfinance (Python)
    → ADLS Gen2 (raw CSV)
        → Databricks Bronze → Silver → Gold
            → Azure Data Factory (daily schedule)
                → Next.js on Vercel (Gold metrics JSON)
                    → [Pivot] refresh JSON / Actions; delete Azure
```

*(Replace this section with a diagram image in Sprint 6.)*

---

## Demo

| Asset | Link |
|--------|------|
| GitHub | https://github.com/HristoDimitrov03/azure-financial-lakehouse |
| Live Vercel dashboard (Gold metrics) | https://azure-financial-lakehouse.vercel.app |

**Pipeline walkthrough** — ADF → Databricks Medallion → Northline Markets dashboard:

https://github.com/user-attachments/assets/7b5db1b7-203f-497d-8e01-989684b592c6

---

## Project structure

```text
azure-financial-lakehouse/
├── web/                 # Next.js Gold dashboard (Vercel root)
├── app/                 # Optional Streamlit scaffold
├── config/              # Tickers & settings (no secrets)
├── src/                 # Python extract / load / utils
├── notebooks/           # Databricks PySpark (incl. 04 extract, 05 Gold CSV export)
├── adf/                 # Data Factory notes / export stubs
├── data/                # Local dry-run + Gold export (gitignored content)
├── scripts/             # Extract, upload, Gold export helpers
├── docs/                # Setup guides & architecture notes
├── tests/               # Unit tests
├── Dockerfile           # Optional container experiments
├── requirements.txt
└── .env.example         # Copy → .env (never commit secrets)
```

---

## Quick start (local — Sprint 0+)

```bash
# 1. Create a virtual environment
python -m venv .venv

# 2. Activate it
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate

# 3. Install dependencies
python -m pip install -r requirements.txt

# 4. Copy env template (fill later when we reach Azure)
copy .env.example .env
```

### Sprint 5 — Next.js dashboard (Vercel)

```powershell
.\.venv\Scripts\Activate.ps1
python scripts\build_gold_export.py
cd web
npm install
npm run dev
```

Deploy: Vercel project with **Root Directory = `web`**.  
Full steps: [`docs/sprint5_vercel.md`](docs/sprint5_vercel.md).

### Sprint 1 — local extract (yfinance)

```bash
# Activate venv, then:
python scripts/run_extract.py

# Optional overrides:
python scripts/run_extract.py --period 6mo
python scripts/run_extract.py --tickers AAPL MSFT SPY
```

Output lands at:

```text
data/raw/market_daily/extract_date=YYYY-MM-DD/market_ohlcv.csv
data/raw/market_daily/extract_date=YYYY-MM-DD/_manifest.json
```

Raw schema columns: `trade_date`, `ticker`, `open`, `high`, `low`, `close`,
`adj_close`, `volume`, `source`, `extracted_at_utc` (see `src/extract/schema.py`).

Edit symbols in `config/tickers.yaml`. No Azure required for this sprint.

### Sprint 2 — ADLS Gen2 upload (Azure Free Trial)

1. Follow [`docs/azure_setup.md`](docs/azure_setup.md) Sprint 2 on your **Free Trial** subscription  
2. Put the **new** `AZURE_STORAGE_CONNECTION_STRING` in `.env`  
3. Upload:

```bash
python scripts/run_extract.py
python scripts/run_upload.py
```

Restart checklist: [`docs/restart_free_trial.md`](docs/restart_free_trial.md)

### Sprint 3 — Databricks Medallion

Portal steps: [`docs/azure_setup.md`](docs/azure_setup.md) Sprint 3.  
Plain English: [`docs/sprint3_databricks.md`](docs/sprint3_databricks.md).

### Sprint 4 — Azure Data Factory

Portal steps: [`docs/azure_setup.md`](docs/azure_setup.md) Sprint 4.  
Plain English: [`docs/sprint4_adf.md`](docs/sprint4_adf.md).  
ADF notes: [`adf/README.md`](adf/README.md).
Notebooks: `notebooks/00`–`03` (Bronze → Silver → Gold). Prefer **Serverless** compute.

---

## Sprint roadmap

| Sprint | Focus |
|--------|--------|
| 0 | Repo foundation |
| 1 | Extraction with `yfinance` |
| 2 | Azure Data Lake Storage Gen2 (**redo on Free Trial**) |
| 3 | Databricks Medallion (after Sprint 2) |
| 4 | Azure Data Factory orchestration (**done** — extract→Medallion + schedule) |
| 5 | Next.js Gold dashboard on Vercel + demo video (**done**) |
| 6 | Portfolio Pivot: export, Docker, free host, README polish |

---

## Tech stack

Python · yfinance · ADLS Gen2 · Databricks / PySpark · Azure Data Factory · Next.js · Vercel · Docker

---

## License

MIT (or your preferred license — finalize before public GitHub push).
