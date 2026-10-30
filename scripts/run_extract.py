"""
CLI entrypoint — Sprint 1 local dry-run extract.

Usage (from repo root, with venv active):
  python scripts/run_extract.py
  python scripts/run_extract.py --period 6mo
  python scripts/run_extract.py --tickers AAPL MSFT
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow `python scripts/run_extract.py` without installing the package
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.extract.yfinance_extractor import extract_market_ohlcv
from src.utils.config import load_settings, load_tickers_config
from src.utils.logging_config import get_logger

logger = get_logger("run_extract")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract daily market OHLCV via yfinance → data/raw (local dry-run).",
    )
    parser.add_argument(
        "--tickers",
        nargs="+",
        default=None,
        help="Override tickers from config/tickers.yaml (e.g. AAPL MSFT).",
    )
    parser.add_argument(
        "--period",
        default=None,
        help="Override history period (e.g. 1mo, 6mo, 1y). Default from tickers.yaml.",
    )
    parser.add_argument(
        "--interval",
        default=None,
        help="Override bar interval (default 1d).",
    )
    parser.add_argument(
        "--extract-date",
        default=None,
        help="Partition date YYYY-MM-DD (default: today UTC).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    tickers_cfg = load_tickers_config()
    settings = load_settings()

    tickers = args.tickers or tickers_cfg["tickers"]
    period = args.period or tickers_cfg["history"]["period"]
    interval = args.interval or tickers_cfg["history"]["interval"]
    raw_root = settings["paths"]["raw_local"]

    logger.info("Starting extract | tickers=%s | period=%s | interval=%s", tickers, period, interval)
    result = extract_market_ohlcv(
        tickers,
        period=period,
        interval=interval,
        raw_root=raw_root,
        extract_date=args.extract_date,
    )

    logger.info(
        "Done | rows=%s | ok=%s | failed=%s | file=%s",
        result.row_count,
        result.tickers_succeeded,
        result.tickers_failed,
        result.output_csv,
    )

    # Non-zero exit if everything failed (CI-friendly)
    if result.row_count == 0:
        logger.error("Extract produced 0 rows.")
        return 1
    if result.tickers_failed:
        logger.warning("Partial success — some tickers failed: %s", result.tickers_failed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
