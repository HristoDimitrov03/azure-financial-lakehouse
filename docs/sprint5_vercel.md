# Sprint 5 — Next.js Gold dashboard on Vercel

## Goal

Public dashboard that shows Gold metrics (`close`, `ma_7d`, `ma_30d`, daily return)
hosted on **Vercel**. Azure still owns the lakehouse; the site reads a static
JSON export for simple free hosting.

## Order

| Step | What |
|------|------|
| **R** | Refresh Gold export JSON (`build_gold_export.py`) |
| **S** | Run Next.js locally (`web/`) |
| **T** | Deploy `web/` to Vercel |
| **U** | (Optional) Silent Loom with dashboard + ADF success |
| **V** | Paste live URL into README Demo table |

## R — Export data the site can read

**Fast path (local extract already on disk):**

```powershell
.\.venv\Scripts\Activate.ps1
python scripts\build_gold_export.py
```

Writes:

- `web/public/data/gold_metrics.json` ← what Next.js / Vercel serves  
- `data/export/gold_metrics.csv`

**Azure Gold path (after a Medallion run):**

1. Databricks → import/run `notebooks/05_export_gold_csv.py`  
2. PC:

```powershell
python scripts\download_gold_export.py
python scripts\build_gold_export.py --csv data\export\gold_metrics.csv
```

## S — Local preview

```powershell
cd web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## T — Vercel

1. Push repo to GitHub (when ready) **or** deploy from CLI / Cursor Vercel MCP  
2. New Vercel project → set **Root Directory** to `web`  
3. Framework: Next.js (auto)  
4. Deploy  

Re-deploy after refreshing `gold_metrics.json` so production shows new days.

## U — Loom (silent OK)

Screen-only recording: ADF Succeeded run → Databricks Job graph → this Vercel URL with ticker + chart.

## Note on Streamlit

`app/streamlit_app.py` stays as an optional scaffold. **Sprint 5 primary UI is Next.js on Vercel.**
