export type GoldRow = {
  trade_date: string;
  ticker: string;
  open?: number | null;
  high?: number | null;
  low?: number | null;
  close: number;
  adj_close?: number | null;
  volume?: number | null;
  ma_7d: number | null;
  ma_30d: number | null;
  daily_return_pct: number | null;
};

export type GoldPayload = {
  generated_at_utc: string;
  /** Medallion / extract completion time when available. */
  pipeline_synced_at_utc?: string | null;
  /** Value shown as Last sync (pipeline stamp, else generated_at). */
  last_synced_at_utc?: string;
  last_synced_source?: string;
  source_file: string;
  row_count: number;
  tickers: string[];
  date_min: string;
  date_max: string;
  rows: GoldRow[];
};
