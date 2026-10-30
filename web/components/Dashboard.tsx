"use client";

import { useMemo, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatInt, formatPct, formatPrice } from "@/lib/format";
import type { GoldPayload, GoldRow } from "@/lib/types";

type Props = {
  data: GoldPayload;
};

function latestRow(rows: GoldRow[]): GoldRow | undefined {
  return [...rows].sort((a, b) => b.trade_date.localeCompare(a.trade_date))[0];
}

export function Dashboard({ data }: Props) {
  const [ticker, setTicker] = useState(data.tickers[0] ?? "AAPL");

  const tickerRows = useMemo(
    () =>
      data.rows
        .filter((r) => r.ticker === ticker)
        .sort((a, b) => a.trade_date.localeCompare(b.trade_date)),
    [data.rows, ticker],
  );

  const latest = latestRow(tickerRows);
  const chartRows = tickerRows.slice(-120);
  const tableRows = [...tickerRows].reverse().slice(0, 12);

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-4 py-10 sm:px-6">
      <header className="flex flex-col gap-4 border-b border-[var(--line)] pb-8 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.22em] text-[var(--muted)]">
            Azure Financial Lakehouse · Gold
          </p>
          <h1 className="mt-2 font-[family-name:var(--font-display)] text-4xl tracking-tight text-[var(--ink)] sm:text-5xl">
            Market metrics
          </h1>
          <p className="mt-3 max-w-xl text-sm leading-relaxed text-[var(--muted)]">
            Daily closes with 7-day / 30-day moving averages from the Medallion
            Gold layer. Data file generated{" "}
            <span className="font-mono text-[var(--ink)]">
              {data.generated_at_utc}
            </span>
            .
          </p>
        </div>
        <label className="flex flex-col gap-2 text-xs font-medium uppercase tracking-wide text-[var(--muted)]">
          Ticker
          <select
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            className="min-w-40 rounded-md border border-[var(--line)] bg-[var(--panel)] px-3 py-2 font-mono text-sm text-[var(--ink)] outline-none focus:border-[var(--accent)]"
          >
            {data.tickers.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>
      </header>

      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Last close" value={formatPrice(latest?.close)} />
        <Stat label="MA 7d" value={formatPrice(latest?.ma_7d)} />
        <Stat label="MA 30d" value={formatPrice(latest?.ma_30d)} />
        <Stat
          label="Daily return"
          value={formatPct(latest?.daily_return_pct)}
          tone={
            (latest?.daily_return_pct ?? 0) >= 0 ? "up" : "down"
          }
        />
      </section>

      <section className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-4 sm:p-6">
        <div className="mb-4 flex items-baseline justify-between gap-3">
          <h2 className="font-[family-name:var(--font-display)] text-xl text-[var(--ink)]">
            {ticker} · close vs moving averages
          </h2>
          <p className="font-mono text-xs text-[var(--muted)]">
            last {chartRows.length} sessions
          </p>
        </div>
        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartRows} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="var(--grid)" strokeDasharray="3 3" />
              <XAxis
                dataKey="trade_date"
                tick={{ fill: "var(--muted)", fontSize: 11 }}
                minTickGap={32}
              />
              <YAxis
                domain={["auto", "auto"]}
                tick={{ fill: "var(--muted)", fontSize: 11 }}
                width={56}
              />
              <Tooltip
                contentStyle={{
                  background: "var(--panel-strong)",
                  border: "1px solid var(--line)",
                  borderRadius: 8,
                  color: "var(--ink)",
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="close"
                name="Close"
                stroke="var(--accent)"
                dot={false}
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="ma_7d"
                name="MA 7d"
                stroke="var(--accent-2)"
                dot={false}
                strokeWidth={1.5}
              />
              <Line
                type="monotone"
                dataKey="ma_30d"
                name="MA 30d"
                stroke="var(--accent-3)"
                dot={false}
                strokeWidth={1.5}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="overflow-hidden rounded-xl border border-[var(--line)] bg-[var(--panel)]">
        <div className="border-b border-[var(--line)] px-4 py-3 sm:px-6">
          <h2 className="font-[family-name:var(--font-display)] text-xl text-[var(--ink)]">
            Recent sessions
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-[var(--panel-strong)] font-mono text-xs uppercase tracking-wide text-[var(--muted)]">
              <tr>
                <th className="px-4 py-3 sm:px-6">Date</th>
                <th className="px-4 py-3">Close</th>
                <th className="px-4 py-3">MA 7d</th>
                <th className="px-4 py-3">MA 30d</th>
                <th className="px-4 py-3">Return</th>
                <th className="px-4 py-3 sm:px-6">Volume</th>
              </tr>
            </thead>
            <tbody>
              {tableRows.map((row) => (
                <tr
                  key={`${row.ticker}-${row.trade_date}`}
                  className="border-t border-[var(--line)]"
                >
                  <td className="px-4 py-2.5 font-mono text-[var(--ink)] sm:px-6">
                    {row.trade_date}
                  </td>
                  <td className="px-4 py-2.5 font-mono">{formatPrice(row.close)}</td>
                  <td className="px-4 py-2.5 font-mono">{formatPrice(row.ma_7d)}</td>
                  <td className="px-4 py-2.5 font-mono">
                    {formatPrice(row.ma_30d)}
                  </td>
                  <td
                    className={`px-4 py-2.5 font-mono ${
                      (row.daily_return_pct ?? 0) >= 0
                        ? "text-[var(--up)]"
                        : "text-[var(--down)]"
                    }`}
                  >
                    {formatPct(row.daily_return_pct)}
                  </td>
                  <td className="px-4 py-2.5 font-mono text-[var(--muted)] sm:px-6">
                    {formatInt(row.volume)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <footer className="border-t border-[var(--line)] pt-6 text-xs text-[var(--muted)]">
        <p>
          Range {data.date_min} → {data.date_max} · {data.row_count.toLocaleString()}{" "}
          Gold rows · refresh with{" "}
          <code className="font-mono text-[var(--ink)]">
            python scripts/build_gold_export.py
          </code>
        </p>
      </footer>
    </div>
  );
}

function Stat({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: "up" | "down";
}) {
  const valueClass =
    tone === "up"
      ? "text-[var(--up)]"
      : tone === "down"
        ? "text-[var(--down)]"
        : "text-[var(--ink)]";

  return (
    <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] px-4 py-4">
      <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-[var(--muted)]">
        {label}
      </p>
      <p className={`mt-2 font-mono text-2xl ${valueClass}`}>{value}</p>
    </div>
  );
}
