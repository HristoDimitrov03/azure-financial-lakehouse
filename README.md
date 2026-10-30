# Azure Financial Market Data Lakehouse

A cloud **batch data platform** for equities: market data is scraped daily, landed in a
data lake, refined through a Medallion pipeline, and surfaced as a public metrics
dashboard (**Northline Markets**).

I built this to run a full Azure lakehouse path end to end — ingest, transform, schedule,
and read the results in a UI I actually use.

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
4. **Orchestrate** — **Azure Data Factory** runs the Databricks Job on a schedule so the lake refreshes without keeping a machine on.
5. **Serve** — Export Gold to JSON and host a **Next.js** dashboard: prices, volume, MA trends, SPY-relative performance, leaderboard, recent sessions. **Last sync** is the real scrape timestamp.

---

## Data flow

```text
yfinance
   → ADLS Gen2 (raw / bronze landing)
      → Databricks: Bronze → Silver → Gold
         → Azure Data Factory (daily Job)
            → Gold export (CSV + pipeline sync stamp)
               → Next.js dashboard
```

**Why batch (daily)?** End-of-day equity analytics need a reliable snapshot, not tick streaming. A once-per-day job is enough for this use case and keeps Azure spend under control.

---

## Toolkit — and why each piece

| Tool | Role in this project | Why it was chosen |
|------|----------------------|-------------------|
| **Python** | Extract scripts, ADLS upload, Gold → JSON export | Natural glue for ingestion and exports; easy to run locally when debugging |
| **yfinance** | Market data source | Free EOD history without a paid market-data feed |
| **Azure Data Lake Storage Gen2** | Durable raw + Delta landing zones | Fits hierarchical lake paths like `extract_date=…` and pairs cleanly with Databricks |
| **Databricks + PySpark** | Medallion transforms | Lakehouse compute where Bronze → Silver → Gold actually runs |
| **Delta Lake** | Bronze / Silver / Gold tables | ACID tables on the lake, schema evolution, safe layer rebuilds |
| **Azure Data Factory** | Schedule + trigger the Databricks Job | Orchestration stays separate from Spark — ADF starts the Job; notebooks do the work |
| **Next.js + Recharts** | Dashboard over Gold | Lightweight UI over curated JSON without opening the lake to the browser |
| **Docker** | Containerized extract + Gold export | Same pipeline steps in a reproducible image (`docker compose run pipeline`) |

---

## Gold metrics the dashboard cares about

| Metric | Meaning |
|--------|---------|
| Close / volume | Latest session price and activity |
| MA 7d / MA 30d | Short- vs medium-term trend (smoothed closes) |
| Daily return % | Session-over-session move |
| vs SPY (indexed) | Stock performance relative to the S&P 500 ETF proxy |
| Last sync | When the extract actually scraped (`extracted_at_utc`), not when a JSON file was rebuilt on a laptop |

Watchlist is configured in `config/tickers.yaml` (AAPL, MSFT, GOOGL, AMZN, META, NVDA, JPM, V, SPY).

---

## Repository map

```text
web/                 Next.js dashboard
notebooks/           Databricks Medallion + daily extract + Gold export
src/                 Python extract / ADLS load helpers
scripts/             Local extract, upload, Gold JSON build / download
adf/                 Data Factory notes
config/              Tickers and non-secret settings
Dockerfile           Extract + Gold export image
docker-compose.yml   Bind-mount pipeline runner
.github/workflows/   Scheduled Gold snapshot refresh
```

---

## Author

**Hristo Dimitrov**  
[LinkedIn](https://www.linkedin.com/in/hristo-dimitrov-0681a8246) · [GitHub](https://github.com/HristoDimitrov03)
