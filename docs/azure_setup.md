# Azure setup guide

> **Active path (Oct 2026):** Azure **Free Trial (~$200 / 30 days)** on a new personal account.  
> Rebuild cloud resources on this subscription. Local code (Sprints 0–1) stays the same.  
> Old Azure for Students resources can be ignored/deleted later — do not mix credentials.

| Sprint | Topic | Status |
|--------|--------|--------|
| 0–1 | Repo + local `yfinance` extract | **DONE** (local — keep using) |
| 2 | Resource group, ADLS Gen2, container, `.env`, upload | **DONE** — `stfinlakehousehd` (North Europe) |
| 3 | Databricks workspace, Serverless/notebooks, Medallion | **DONE** — UC external location + 01→02→03 |
| 4 | Data Factory daily orchestration | **DONE** — Job extract→Medallion + ADF schedule |
| 5 | Next.js Gold dashboard on Vercel + Loom | **NOW** — see `docs/sprint5_vercel.md` |
| 6 | Export polish, free host forever, **delete Azure** | TODO |

### Cost rules (Free Trial)

- Prefer **one region** for RG + Storage + Databricks + ADF.
- Free Trial can block some regions (`RequestDisallowedByAzure` / “not accepting new customers”).
  If **West Europe** fails, try in order: **North Europe**, **France Central**, **Germany West Central**, **Sweden Central**, **East US**, **UK South**.
- Databricks: use **Serverless** for notebooks when available; otherwise a **Single Node** cluster with **Terminate after 30 minutes**.
- Stop / delete compute when not demoing. Delete the resource group in Sprint 6.

---

## Sprint 2 — ADLS Gen2 (Free Trial restart)

### What you create

1. Resource group `rg-financial-lakehouse`
2. Storage account (ADLS Gen2, Hierarchical namespace **Enabled**)
3. Container `market-data`
4. Connection string in local `.env`
5. Upload of raw extract CSV

### Step A — Sign in (new account)

1. Open [https://portal.azure.com](https://portal.azure.com)
2. Sign in with the **Free Trial** Microsoft account (not the Students one)
3. Confirm the top subscription picker shows your **Free Trial** subscription

### Step B — Resource group

1. Search → **Resource groups** → **+ Create**
2. Subscription: Free Trial
3. Name: `rg-financial-lakehouse`
4. Region: pick one that validates (see region note above). Reuse that same region for storage + Databricks.
5. Review + create → Create

### Step C — Storage account (ADLS Gen2)

1. Search → **Storage accounts** → **+ Create**
2. Resource group: `rg-financial-lakehouse`
3. Name: globally unique, e.g. `stfinlakehouse` + your initials
4. Region: **same as RG**
5. Primary service: **Azure Blob Storage or Azure Data Lake Storage**
6. Performance: **Standard** · Redundancy: **LRS**
7. Advanced → **Hierarchical namespace: Enable**
8. Review + create → Create → Go to resource

Skip optional “Primary workload” if you want.

### Step D — Container

1. Storage account → **Containers** → **+ Container**
2. Name: `market-data` · Access: **Private** → Create

### Step E — Connection string → `.env`

1. Storage account → **Access keys** → Show → copy **Connection string**
2. Update project `.env` (replace old Students values):

```env
AZURE_STORAGE_ACCOUNT_NAME=your_new_storage_account
AZURE_STORAGE_CONTAINER=market-data
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net
```

Never paste keys into chat or GitHub.

### Step F — Extract + upload

```powershell
cd C:\Users\hrist\Desktop\W\Cursor_Projects\azure-financial-lakehouse
.\.venv\Scripts\Activate.ps1
python scripts/run_extract.py
python scripts/run_upload.py
```

### Step G — Verify

Containers → `market-data` → `bronze` → `market_daily` → `extract_date=...`  
Expect `market_ohlcv.csv` and `_manifest.json`.

### Sprint 2 checklist

- [x] Free Trial subscription selected in portal
- [x] RG + ADLS Gen2 `stfinlakehousehd` + `market-data` (North Europe)
- [x] `.env` points at new storage
- [x] `run_upload.py` succeeds
- [x] Files visible under `bronze/market_daily/...`

---

## Sprint 3 — Databricks Medallion (Free Trial)

Do these steps **in order**. Letters are sequential: **H → I → J → K → L**.

| Step | Name | Outcome |
|------|------|---------|
| **H** | Create Databricks workspace | You can **Launch Workspace** |
| **I** | Import notebooks | Four notebooks in one folder `lakehouse` |
| **J** | Connect compute | Notebook shows **Serverless** (or `lakehouse-dev`) |
| **K** | Link ADLS via Unity Catalog | External location can list `bronze/` |
| **L** | Run Medallion | Bronze → Silver → Gold succeed |

Storage already in place: account **`stfinlakehousehd`**, container **`market-data`**, region **North Europe**.

---

### Step H — Create Databricks workspace

1. Portal → Free Trial account → **Azure Databricks** → **+ Create**
2. Resource group: `rg-financial-lakehouse`
3. Workspace name: `dbw-financial-lakehouse`
4. Region: **North Europe**
5. Pricing tier: **Premium (+ Role-based access controls)**  
   - Do **not** pick Databricks **Trial** (blocked on Free Trial and Students)
6. Workspace type: **Hybrid**
7. Review + create → Create → wait → **Go to resource** → **Launch Workspace**

**Step H done when:** Databricks home page opens (left menu: Workspace, Catalog, Compute, …).

---

### Step I — Import notebooks

All four must be in the **same** folder so `%run ./00_config_and_auth` works.

**Files on your PC:**

```text
C:\Users\hrist\Desktop\W\Cursor_Projects\azure-financial-lakehouse\notebooks\
  00_config_and_auth.py
  01_bronze_ingestion.py
  02_silver_cleansing.py
  03_gold_metrics.py
```

1. In Databricks → left **Workspace**
2. Open **Users** → your email (or Home)
3. **Create** → **Folder** → name: `lakehouse` → open it
4. In that folder → **Import** → choose each `.py` file (one by one or as allowed)
5. Confirm you see four notebooks: `00_config_and_auth`, `01_bronze_ingestion`, `02_silver_cleansing`, `03_gold_metrics`

**Step I done when:** all four are inside `Users/<you>/lakehouse/`.

---

### Step J — Connect compute

Open `01_bronze_ingestion` (from the `lakehouse` folder).

**Preferred — Serverless**

1. Top bar → **Connect** (or compute dropdown)
2. Click **Serverless** if listed  
3. Or run a tiny cell / **Run all** and let it auto-attach Serverless (common on Unity Catalog)

**Fallback — only if Serverless is missing**

1. Left **Compute** → **All-purpose compute** → **Create**
2. Name: `lakehouse-dev` · **Single node** · small size · Terminate after **30** minutes
3. Wait until **Running** → notebook **Connect** → select `lakehouse-dev`

Do **not** create multi-node / huge Job clusters.

**Step J done when:** notebook top bar shows **Serverless** or **lakehouse-dev** (not plain “Connect”).

---

### Step K — Link ADLS for Serverless (Unity Catalog)

Serverless **cannot** use `spark.conf` account keys (`CONFIG_NOT_AVAILABLE`).  
Use an **Access Connector** + **external location** instead.

#### K1 — Access Connector (Azure Portal)

1. Portal → **+ Create a resource** → search **Azure Databricks Access Connector** → Create  
2. Subscription: Free Trial · Resource group: `rg-financial-lakehouse`  
3. Name: `ac-finlakehouse` · Region: **North Europe**  
4. Review + create → wait → open the resource  
5. Left **Identity** → note that **System assigned** is **On** (copy the Object/Principal ID if shown)

#### K2 — Grant storage access (Azure Portal)

1. Portal → storage **`stfinlakehousehd`** → **Access Control (IAM)** → **+ Add** → **Add role assignment**  
2. Role: **Storage Blob Data Contributor** → Next  
3. Members: **Managed identity** → **+ Select members**  
4. Pick **Azure Databricks Access Connector** → select **`ac-finlakehouse`** → Select → Review + assign  

Wait ~1–2 minutes for RBAC to propagate.

#### K3 — Storage credential + external location (Databricks)

1. Databricks → left **Catalog**  
2. Gear / **External Data** (or **+** → create external location — UI varies slightly)  
3. Create a **storage credential**:
   - Auth: **Azure managed identity** / Access Connector  
   - Paste the Access Connector **resource ID** from Portal → `ac-finlakehouse` → **JSON View** → `id`  
     (looks like `/subscriptions/.../accessConnectors/ac-finlakehouse`)  
4. Create an **external location**:
   - URL: `abfss://market-data@stfinlakehousehd.dfs.core.windows.net/`  
   - Credential: the one you just created  
5. Use **Test connection** / **Browse** if the UI offers it — should see `bronze/`

#### K4 — Notebook widgets (no key needed)

1. Re-import updated `00_config_and_auth.py` from your PC (overwrite)  
2. Open `00` → set widgets:
   - `storage_account` = `stfinlakehousehd`
   - `container` = `market-data`
   - leave `storage_key_fallback` **empty**  
3. **Run all** on `00` — connectivity cell should list bronze folders  

**Step K done when:** `00` lists `RAW_CSV_ROOT` without `CONFIG_NOT_AVAILABLE`.

**Classic cluster only (optional):** if you connect `lakehouse-dev` instead of Serverless, you may paste **key1** into `storage_key_fallback` and skip K1–K3.

---

### Step L — Run Bronze → Silver → Gold

With compute connected and widgets set:

1. Open `01_bronze_ingestion` → **Run all** → wait until success  
2. Open `02_silver_cleansing` → **Run all** → wait until success  
3. Open `03_gold_metrics` → **Run all** → wait until success  

**Success checks:**

- Notebook previews show rows  
- Gold preview includes columns `ma_7d` and `ma_30d`  
- ADLS container `market-data` has:
  - `bronze/delta/market_ohlcv`
  - `silver/delta/market_ohlcv`
  - `gold/delta/market_metrics`

**Step L done when:** all three notebooks succeeded and Gold paths exist in the lake.

---

### Sprint 3 checklist

- [x] **H** Workspace launched (North Europe, Premium, Hybrid)
- [x] **I** Four notebooks in folder `lakehouse`
- [x] **J** Serverless or `lakehouse-dev` connected
- [x] **K** Access Connector + UC external location; `00` lists bronze
- [x] **L** Bronze, Silver, Gold all succeeded

---

## Sprint 4 — Azure Data Factory (orchestrate Medallion)

Same subscription / RG / region as before:

- Resource group: `rg-financial-lakehouse`
- Region: **North Europe**
- Storage: `stfinlakehousehd` · container `market-data`
- Databricks: `dbw-financial-lakehouse`
- UC external location: `ext_market_data` (already done — jobs reuse it)

ADF does **not** replace Databricks. It **starts** a Databricks Job on a schedule.

Letters continue: **M → N → O → P → Q**.

---

### Step M — Create Data Factory

1. Portal → [https://portal.azure.com](https://portal.azure.com) → Free Trial subscription  
2. **+ Create a resource** → search **Data Factory** → Create  
3. Basics:
   - Subscription: Free Trial  
   - Resource group: `rg-financial-lakehouse`  
   - Name: `adf-financial-lakehouse`  
   - Region: **North Europe**  
   - Version: **V2**  
4. Leave Git config **unconfigured** for now (faster for learning; wire Git later if you want)  
5. Review + create → Create → wait → **Go to resource** → **Launch Studio**  

**Step M done when:** Azure Data Factory Studio opens (Author / Monitor / Manage).

---

### Step N — Databricks access token + ADF linked service

ADF needs permission to start jobs in your workspace.

#### N1 — Databricks personal access token (PAT)

1. Databricks workspace → your avatar (top right) → **Settings** → **Developer**  
   (or User Settings → Access tokens — UI label varies)  
2. **Generate new token**  
   - Comment: `adf-sprint4`  
   - Lifetime: **30 days** (enough for Free Trial demo; rotate/delete after)  
3. **Copy the token once** → store only in ADF (never commit to Git / chat)

#### N2 — Linked service in ADF Studio

1. ADF Studio → left **Manage** (toolbox) → **Linked services** → **+ New**  
2. Search **Azure Databricks** → Continue  
3. Name: `ls_databricks`  
4. **Account selection method:** pick your Databricks workspace  
   - Subscription + Databricks workspace: `dbw-financial-lakehouse`  
5. **Authentication:** Access Token → paste the PAT from N1  
6. **Cluster / compute:** choose **Serverless** (or “New job cluster” only if Serverless is missing — keep it tiny / auto-terminate)  
7. **Test connection** → should succeed → **Create**

**Step N done when:** `ls_databricks` shows Connected / test OK.

---

### Step O — Databricks Job (extract + Medallion)

Create the work ADF will call. Prefer one **Job** with four notebook tasks.

**First:** import `notebooks/04_daily_extract_to_adls.py` into the same `lakehouse` folder (with `00`–`03`).

1. Databricks → left **Workflows** (or **Jobs & Pipelines**) → **Create job** (or edit `job_medallion_market`)  
2. Job name: `job_medallion_market`  
3. **Task 1 — extract (live market data)**
   - Name: `extract`  
   - Type: **Notebook**  
   - Path: `/Users/<your-email>/lakehouse/04_daily_extract_to_adls`  
   - Compute: **Serverless**  
4. **Add task → bronze**
   - Path: `.../lakehouse/01_bronze_ingestion`  
   - Depends on: `extract`  
   - Serverless  
5. **Add task → silver**
   - Path: `.../lakehouse/02_silver_cleansing`  
   - Depends on: `bronze`  
6. **Add task → gold**
   - Path: `.../lakehouse/03_gold_metrics`  
   - Depends on: `silver`  
7. Save → **Run now** once → all **four** tasks green  

Widgets: defaults (`stfinlakehousehd` / `market-data`, empty key). UC external location + `%run ./00_config_and_auth` handle ADLS.

**If the Job already has bronze→silver→gold only:** **+ Add task** for `04`, set it as the **first** task, and make `bronze` depend on `extract` (not nothing).

**Step O done when:** Job runs `extract → bronze → silver → gold` successfully.

---

### Step P — ADF pipeline calls the Job

1. ADF Studio → **Author** (pencil) → **Pipelines** → **+** → **Pipeline**  
2. Name: `pl_daily_medallion`  
3. Activities pane → search **Databricks**  
4. Prefer **Databricks Job** activity (starts your Workflow).  
   If your Studio only shows **Notebook** activity, use three Notebook activities chained `01 → 02 → 03` with the same linked service instead.  
5. Drop **Databricks Job** on the canvas → select it  
6. **Azure Databricks** tab → Linked service: `ls_databricks`  
7. **Settings** tab → Job: select `job_medallion_market`  
8. **Publish all** (top) — required so Trigger can run the saved pipeline  

**Step P done when:** pipeline published with one Job activity (or three chained Notebook activities).

---

### Step Q — Trigger now + optional schedule

#### Q1 — Manual run (required)

1. Open `pl_daily_medallion` → **Add trigger** → **Trigger now** (or Debug if you prefer a debug run)  
2. ADF Studio → **Monitor** → Pipeline runs → wait until **Succeeded**  
3. Databricks → Workflows → `job_medallion_market` → recent run **Succeeded**

#### Q2 — Daily schedule (optional for portfolio)

1. Pipeline → **Add trigger** → **New/Edit** → **Schedule**  
2. Name: `tr_daily_medallion`  
3. Recurrence: every **1 Day** · pick a quiet UTC hour (e.g. 06:00)  
4. Start date = today · no end (or end when Free Trial ends)  
5. OK → **Publish all**

**Cost tip:** Disable or delete the schedule when not demoing so Databricks does not run daily idle burns.

With notebook **04** first in the Job, each scheduled run pulls **new yfinance data** then rebuilds Medallion — no PC required.

**Step Q done when:** at least one ADF-triggered run succeeded end-to-end (ideally after 04 is in the Job).

---

### Sprint 4 checklist

- [x] **M** Data Factory `adf-financial-lakehouse` + Studio open  
- [x] **N** PAT + linked service `ls_databricks` test OK  
- [x] **O** Job `job_medallion_market` (`extract`→`bronze`→`silver`→`gold`)  
- [x] **P** Pipeline `pl_daily_medallion` published  
- [x] **Q** ADF trigger Succeeded + daily schedule + ADLS OK

### After Sprint 4 (optional Git export)

ADF Studio → pipeline → view JSON / ARM template → save under `adf/pipelines/` for GitHub (see `adf/README.md`).

---

## Historical note (Azure for Students)

Students path hit: region policy quirks, VM family quota `0`, and no Serverless in notebook/job pickers.  
That attempt is abandoned for compute. Free Trial is the supported cloud path going forward.

---

## Sprint 6 reminder

After Loom + Gold export for Streamlit: delete resource group `rg-financial-lakehouse` so Free Trial credit is not burned by idle Databricks/storage.
