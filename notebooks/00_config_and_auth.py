# Databricks notebook source
# MAGIC %md
# MAGIC # 00 — Config & ADLS authentication
# MAGIC Run this **once per cluster session** before Bronze / Silver / Gold.
# MAGIC
# MAGIC **Serverless (recommended on Free Trial):** access ADLS via a Unity Catalog
# MAGIC **external location** (Access Connector). No account key in the notebook.
# MAGIC
# MAGIC **Classic cluster fallback:** account key via TEMP widget / secret + `spark.conf`.
# MAGIC
# MAGIC Portal steps: `docs/azure_setup.md` → Sprint 3 → Step K.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Widgets (edit defaults if your names differ)

# COMMAND ----------

dbutils.widgets.text("storage_account", "stfinlakehousehd", "Storage account name")
dbutils.widgets.text("container", "market-data", "Container name")
dbutils.widgets.text("secret_scope", "lakehouse", "Databricks secret scope")
dbutils.widgets.text("secret_key_name", "storage-access-key", "Secret name for account key")
# Classic-cluster learning fallback only — leave empty on Serverless + UC.
dbutils.widgets.text("storage_key_fallback", "", "TEMP account key (classic cluster only)")

storage_account = dbutils.widgets.get("storage_account").strip()
container = dbutils.widgets.get("container").strip()
secret_scope = dbutils.widgets.get("secret_scope").strip()
secret_key_name = dbutils.widgets.get("secret_key_name").strip()
storage_key_fallback = dbutils.widgets.get("storage_key_fallback").strip()

assert storage_account, "storage_account widget is empty"
assert container, "container widget is empty"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Authenticate Spark → ADLS Gen2
# MAGIC Serverless ignores `fs.azure.account.key` — UC external location must cover the path.
# MAGIC Classic clusters can still use the TEMP widget / secret.

# COMMAND ----------

base_abfss = f"abfss://{container}@{storage_account}.dfs.core.windows.net"

# Hive-style CSV landing zone (Sprint 2 upload target)
RAW_CSV_ROOT = f"{base_abfss}/bronze/market_daily"

# Delta table locations on the lake (Medallion)
BRONZE_DELTA = f"{base_abfss}/bronze/delta/market_ohlcv"
SILVER_DELTA = f"{base_abfss}/silver/delta/market_ohlcv"
GOLD_DELTA = f"{base_abfss}/gold/delta/market_metrics"

# Optional metastore table names (workspace default catalog/schema)
BRONZE_TABLE = "bronze_market_ohlcv"
SILVER_TABLE = "silver_market_ohlcv"
GOLD_TABLE = "gold_market_metrics"

account_key = None
if storage_key_fallback:
    account_key = storage_key_fallback
    print("Using TEMP storage_key_fallback widget — clear it after the demo.")
else:
    try:
        account_key = dbutils.secrets.get(scope=secret_scope, key=secret_key_name)
        print(f"Using secret {secret_scope}/{secret_key_name}")
    except Exception:  # noqa: BLE001 — secret optional on Serverless + UC
        print(
            "No account key (secret/widget). OK if Unity Catalog external location "
            "covers this storage path (required for Serverless)."
        )

if account_key:
    conf_name = f"fs.azure.account.key.{storage_account}.dfs.core.windows.net"
    try:
        spark.conf.set(conf_name, account_key)
        print(f"Set Spark config {conf_name}")
    except Exception as conf_exc:  # noqa: BLE001
        msg = str(conf_exc)
        if "CONFIG_NOT_AVAILABLE" in msg or "not available" in msg.lower():
            print(
                "Serverless blocked account-key spark.conf (expected). "
                "Relying on Unity Catalog external location instead."
            )
        else:
            raise

print("Path config ready.")
print(f"RAW_CSV_ROOT = {RAW_CSV_ROOT}")
print(f"BRONZE_DELTA = {BRONZE_DELTA}")
print(f"SILVER_DELTA = {SILVER_DELTA}")
print(f"GOLD_DELTA   = {GOLD_DELTA}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Quick connectivity check
# MAGIC Lists the bronze CSV landing folder. If this fails on Serverless, finish Step K
# MAGIC (Access Connector + external location) in `docs/azure_setup.md`.

# COMMAND ----------

try:
    display(dbutils.fs.ls(RAW_CSV_ROOT))
except Exception as ls_exc:  # noqa: BLE001
    raise RuntimeError(
        "Cannot list ADLS path. On Serverless: create Access Connector + UC external "
        f"location for {base_abfss}/ (see azure_setup.md Step K). "
        "On a classic cluster: paste key1 into storage_key_fallback and re-run."
    ) from ls_exc
