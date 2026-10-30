# Azure Financial Market Data Lakehouse

A cloud **batch data platform** for equities: market data is scraped daily, landed in a
data lake, refined through a Medallion pipeline, and surfaced as a public metrics
dashboard (**Northline Markets**).

Built to demonstrate end-to-end data engineering on Azure — not a tutorial clone of every sprint step.

---

## See it live

| | |
|--|--|
| **Dashboard** | https://azure-financial-lakehouse.vercel.app |
| **Repository** | https://github.com/HristoDimitrov03/azure-financial-lakehouse |

**How the platform runs** — Azure Data Factory triggers Databricks (extract → Bronze → Silver → Gold), then curated metrics appear on the site:

https://github.com/user-attachments/assets/7b5db1b7-203f-497d-8e01-989684b592c6

---

## What it does

1. **Ingest** — Pull daily OHLCV for a watchlist of large-cap stocks plus **SPY** (S&P 500 ETF benchmark) via `yfinance`.
2. **Land** — Store raw extracts in **ADLS Gen2**, partitioned by extract date, with a scrape-time manifest (`extracted_at_utc`).
3. **Refine (Medallion)** — Databricks / PySpark:
   - **Bronze** — faithful raw landing  
   - **Silver** — typed, deduplicated, trustworthy  
   - **Gold** — dashboard metrics (7d / 30d moving averages, daily returns)
4. **Orchestrate** — **Azure Data Factory** runs the Databricks Job on a schedule so the lake refreshes without a laptop.
5. **Serve** — Export Gold to JSON and host **Next.js** on **Vercel**: prices, volume, MA trends, SPY-relative performance, leaderboard, recent sessions. **Last sync** on the UI is the real scrape timestamp.

---

## Data flow

```text
yfinance
   → ADLS Gen2 (raw / bronze landing)
      → Databricks: Bronze → Silver → Gold (Serverless + Unity Catalog)
         → Azure Data Factory (daily Job)
            → Gold export (CSV + pipeline sync stamp)
               → Next.js dashboard on Vercel
```

**Why batch (daily)?** End-of-day equity analytics need a reliable snapshot, not tick streaming. That matches common junior DE/DA workloads and keeps cloud cost predictable on Free Trial.

---

## Toolkit — and why each piece

| Tool | Role in this project | Why it was chosen |
|------|----------------------|-------------------|
| **Python** | Extract scripts, ADLS upload, Gold → JSON export | Standard DE glue language; easy local dry-runs and CI-friendly scripts |
| **yfinance** | Market data source | Free, practical EOD history for a portfolio demo without paid market-data licenses |
| **Azure Data Lake Storage Gen2** | Durable raw + Delta landing zones | Industry-standard Azure lake storage; hierarchical namespace fits `extract_date=…` partitions |
| **Databricks + PySpark** | Medallion transforms at scale | Real lakehouse compute; Serverless + Unity Catalog show modern Azure Databricks practice |
| **Delta Lake** | Bronze / Silver / Gold tables | ACID tables on the lake, schema evolution, overwrite-safe layer rebuilds |
| **Azure Data Factory** | Schedule + trigger the Databricks Job | Separates orchestration from compute — ADF starts work; Spark does the transforms |
| **Unity Catalog / Access Connector** | Secure lake access from Databricks | Avoids brittle secret-based mounts; aligns with current Databricks security model |
| **Next.js + Recharts** | Public “product” UI over Gold | Fast, static-friendly frontend that reads curated JSON without exposing the lake |
| **Vercel** | Host the dashboard | Zero-ops public URL for recruiters; Root Directory `web/` keeps the monorepo clean |
| **GitHub** | Source of truth + demo video | Portfolio entry point; video proves the live Azure path |

Setup runbooks (if you want to reproduce the cloud path) live under [`docs/`](docs/) — the README stays focused on **what** and **why**.

---

## Gold metrics the dashboard cares about

| Metric | Meaning |
|--------|---------|
| Close / volume | Latest session price and activity |
| MA 7d / MA 30d | Short- vs medium-term trend (smoothed closes) |
| Daily return % | Session-over-session move |
| vs SPY (indexed) | Stock performance relative to the S&P 500 ETF proxy |
| Last sync | When the extract actually scraped (`extracted_at_utc`), not “when someone rebuilt a JSON file” |

Watchlist is configured in `config/tickers.yaml` (AAPL, MSFT, GOOGL, AMZN, META, NVDA, JPM, V, SPY).

---

## Repository map (orientation)

```text
web/           Next.js dashboard (Vercel)
notebooks/     Databricks Medallion + daily extract + Gold export
src/           Python extract / ADLS load helpers
scripts/       Local extract, upload, Gold JSON build / download
adf/           Data Factory notes
docs/          Architecture & Azure setup guides
config/        Tickers and non-secret settings
```

---

## License

MIT
