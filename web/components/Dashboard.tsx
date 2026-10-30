"use client";

import { useMemo, useState } from "react";
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ThemeToggle } from "@/components/ThemeToggle";
import {
  formatLastSyncEet,
  formatPct,
  formatPrice,
} from "@/lib/format";
import type { GoldPayload, GoldRow } from "@/lib/types";

type Props = {
  data: GoldPayload;
};

type LeaderRow = {
  ticker: string;
  close: number;
  daily_return_pct: number | null;
  trade_date: string;
};

function latestRow(rows: GoldRow[]): GoldRow | undefined {
  return [...rows].sort((a, b) => b.trade_date.localeCompare(a.trade_date))[0];
}

export function Dashboard({ data }: Props) {
  const [ticker, setTicker] = useState(
    data.tickers.find((t) => t !== "SPY") ?? data.tickers[0] ?? "AAPL",
  );

  const tickerRows = useMemo(
    () =>
      data.rows
        .filter((r) => r.ticker === ticker)
        .sort((a, b) => a.trade_date.localeCompare(b.trade_date)),
    [data.rows, ticker],
  );

  const spyByDate = useMemo(() => {
    const map = new Map<string, number>();
    for (const row of data.rows) {
      if (row.ticker === "SPY") map.set(row.trade_date, row.close);
    }
    return map;
  }, [data.rows]);

  const hasSpy = spyByDate.size > 0;

  const latest = latestRow(tickerRows);
  const chartRows = tickerRows.slice(-120);
  const tableRows = [...tickerRows].reverse().slice(0, 12);

  const leaderboard = useMemo(() => {
    const byTicker = new Map<string, GoldRow[]>();
    for (const row of data.rows) {
      const list = byTicker.get(row.ticker) ?? [];
      list.push(row);
      byTicker.set(row.ticker, list);
    }
    const rows: LeaderRow[] = [];
    for (const [sym, list] of byTicker) {
      const last = latestRow(list);
      if (!last) continue;
      rows.push({
        ticker: sym,
        close: last.close,
        daily_return_pct: last.daily_return_pct,
        trade_date: last.trade_date,
      });
    }
    return rows.sort(
      (a, b) =>
        (b.daily_return_pct ?? -Infinity) - (a.daily_return_pct ?? -Infinity),
    );
  }, [data.rows]);

  const leaderDate = leaderboard[0]?.trade_date;

  const spyCompareRows = useMemo(() => {
    if (!hasSpy || chartRows.length === 0) return [];
    const first = chartRows[0];
    const spyFirst = spyByDate.get(first.trade_date);
    if (!first.close || !spyFirst) return [];

    return chartRows.map((row) => {
      const spyClose = spyByDate.get(row.trade_date);
      return {
        trade_date: row.trade_date,
        ticker_indexed: (row.close / first.close) * 100,
        spy_indexed:
          spyClose !== undefined ? (spyClose / spyFirst) * 100 : null,
      };
    });
  }, [chartRows, hasSpy, spyByDate]);

  const vsSpyLatest = spyCompareRows.length
    ? spyCompareRows[spyCompareRows.length - 1]
    : null;
  const vsSpyPct =
    vsSpyLatest && vsSpyLatest.spy_indexed != null
      ? vsSpyLatest.ticker_indexed - vsSpyLatest.spy_indexed
      : null;

  const lastSync = formatLastSyncEet(
    data.last_synced_at_utc ??
      data.pipeline_synced_at_utc ??
      data.generated_at_utc,
  );

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-4 py-10 sm:px-6">
      <div className="flex justify-end">
        <ThemeToggle />
      </div>

      <header className="flex flex-col gap-4 border-b border-[var(--line)] pb-8 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.22em] text-[var(--muted)]">
            Northline Markets
          </p>
          <h1 className="mt-2 font-[family-name:var(--font-display)] text-4xl tracking-tight text-[var(--ink)] sm:text-5xl">
            Equities at a glance
          </h1>
          <p className="mt-3 max-w-xl text-sm leading-relaxed text-[var(--muted)]">
            Follow daily prices, trend averages, trading volume, and how each
            name stacks up against the S&amp;P 500.
          </p>
          <div
            className="mt-4 inline-flex items-center gap-2 rounded-full border border-[var(--line)] bg-[var(--panel)] px-3 py-1.5 text-sm"
            title="When market data was last scraped (yfinance extract time)"
          >
            <span
              className="h-2 w-2 shrink-0 rounded-full bg-[var(--accent)]"
              aria-hidden
            />
            <span className="text-[var(--muted)]">Last sync:</span>
            <span className="font-medium text-[var(--ink)]">{lastSync}</span>
          </div>
        </div>
        <label className="flex flex-col gap-2 text-xs font-medium uppercase tracking-wide text-[var(--muted)]">
          Stock
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
        <Stat
          label="MA 7d"
          value={formatPrice(latest?.ma_7d)}
          info="7-day moving average: the average closing price over the last 7 trading days. Smooths short-term noise so you see the recent trend."
        />
        <Stat
          label="MA 30d"
          value={formatPrice(latest?.ma_30d)}
          info="30-day moving average: the average closing price over the last 30 trading days. Shows a longer, slower trend than the 7-day average."
        />
        <Stat
          label="Daily return"
          value={formatPct(latest?.daily_return_pct)}
          tone={(latest?.daily_return_pct ?? 0) >= 0 ? "up" : "down"}
        />
      </section>

      <section className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-4 sm:p-6">
        <div className="mb-4 flex items-baseline justify-between gap-3">
          <h2 className="font-[family-name:var(--font-display)] text-xl text-[var(--ink)]">
            {ticker} · close, MAs & volume
          </h2>
          <p className="font-mono text-xs text-[var(--muted)]">
            last {chartRows.length} sessions
          </p>
        </div>
        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart
              data={chartRows}
              margin={{ top: 8, right: 12, left: 0, bottom: 0 }}
            >
              <CartesianGrid stroke="var(--grid)" strokeDasharray="3 3" />
              <XAxis
                dataKey="trade_date"
                tick={{ fill: "var(--muted)", fontSize: 11 }}
                minTickGap={32}
              />
              <YAxis
                yAxisId="price"
                domain={["auto", "auto"]}
                tick={{ fill: "var(--muted)", fontSize: 11 }}
                width={56}
              />
              <YAxis
                yAxisId="vol"
                orientation="right"
                tick={{ fill: "var(--muted)", fontSize: 10 }}
                width={48}
                tickFormatter={(v) =>
                  v >= 1_000_000
                    ? `${(v / 1_000_000).toFixed(1)}M`
                    : v >= 1000
                      ? `${(v / 1000).toFixed(0)}K`
                      : String(v)
                }
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
              <Bar
                yAxisId="vol"
                dataKey="volume"
                name="Volume"
                fill="var(--grid)"
                opacity={0.85}
              />
              <Line
                yAxisId="price"
                type="monotone"
                dataKey="close"
                name="Close"
                stroke="var(--accent)"
                dot={false}
                strokeWidth={2}
              />
              <Line
                yAxisId="price"
                type="monotone"
                dataKey="ma_7d"
                name="MA 7d"
                stroke="var(--accent-2)"
                dot={false}
                strokeWidth={1.5}
              />
              <Line
                yAxisId="price"
                type="monotone"
                dataKey="ma_30d"
                name="MA 30d"
                stroke="var(--accent-3)"
                dot={false}
                strokeWidth={1.5}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </section>

      {hasSpy && ticker !== "SPY" && spyCompareRows.length > 0 && (
        <section className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-4 sm:p-6">
          <div className="mb-4 flex flex-wrap items-baseline justify-between gap-3">
            <h2 className="font-[family-name:var(--font-display)] text-xl text-[var(--ink)]">
              {ticker} vs SPY (indexed)
            </h2>
            <p className="font-mono text-xs text-[var(--muted)]">
              both start at 100 ·{" "}
              <span
                className={
                  (vsSpyPct ?? 0) >= 0 ? "text-[var(--up)]" : "text-[var(--down)]"
                }
              >
                {vsSpyPct !== null
                  ? `${vsSpyPct >= 0 ? "+" : ""}${vsSpyPct.toFixed(1)} pts vs SPY`
                  : "—"}
              </span>
            </p>
          </div>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={spyCompareRows}
                margin={{ top: 8, right: 12, left: 0, bottom: 0 }}
              >
                <CartesianGrid stroke="var(--grid)" strokeDasharray="3 3" />
                <XAxis
                  dataKey="trade_date"
                  tick={{ fill: "var(--muted)", fontSize: 11 }}
                  minTickGap={32}
                />
                <YAxis
                  domain={["auto", "auto"]}
                  tick={{ fill: "var(--muted)", fontSize: 11 }}
                  width={48}
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
                  dataKey="ticker_indexed"
                  name={ticker}
                  stroke="var(--accent)"
                  dot={false}
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="spy_indexed"
                  name="SPY"
                  stroke="var(--accent-2)"
                  dot={false}
                  strokeWidth={1.75}
                  strokeDasharray="4 4"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-3 text-xs text-[var(--muted)]">
            Indexed to the first session in the chart window so different price
            levels are comparable. SPY is the S&amp;P 500 ETF benchmark in your
            extract list.
          </p>
        </section>
      )}

      {ticker === "SPY" && (
        <p className="rounded-xl border border-[var(--line)] bg-[var(--panel)] px-4 py-3 text-sm text-[var(--muted)]">
          SPY is the benchmark — pick another ticker to see the vs-SPY comparison
          chart.
        </p>
      )}

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-5">
        <div className="overflow-hidden rounded-xl border border-[var(--line)] bg-[var(--panel)] lg:col-span-1">
          <div className="border-b border-[var(--line)] px-3 py-3">
            <h2 className="font-[family-name:var(--font-display)] text-lg text-[var(--ink)]">
              Leaderboard
            </h2>
            <p className="mt-1 font-mono text-[10px] text-[var(--muted)]">
              {leaderDate ?? "—"} · click row
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-[var(--panel-strong)] font-mono text-[10px] uppercase tracking-wide text-[var(--muted)]">
                <tr>
                  <th className="px-2 py-2">#</th>
                  <th className="px-2 py-2">Tkr</th>
                  <th className="px-2 py-2">Ret</th>
                </tr>
              </thead>
              <tbody>
                {leaderboard.map((row, idx) => (
                  <tr
                    key={row.ticker}
                    onClick={() => setTicker(row.ticker)}
                    className={`cursor-pointer border-t border-[var(--line)] transition-colors hover:bg-[var(--panel-strong)] ${
                      row.ticker === ticker ? "bg-[var(--panel-strong)]" : ""
                    }`}
                  >
                    <td className="px-2 py-2 font-mono text-xs text-[var(--muted)]">
                      {idx + 1}
                    </td>
                    <td className="px-2 py-2 font-mono text-xs text-[var(--ink)]">
                      {row.ticker}
                    </td>
                    <td
                      className={`px-2 py-2 font-mono text-xs ${
                        (row.daily_return_pct ?? 0) >= 0
                          ? "text-[var(--up)]"
                          : "text-[var(--down)]"
                      }`}
                    >
                      {formatPct(row.daily_return_pct)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="overflow-hidden rounded-xl border border-[var(--line)] bg-[var(--panel)] lg:col-span-4">
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
                  <th className="px-4 py-3 sm:px-6">Return</th>
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
                    <td className="px-4 py-2.5 font-mono">
                      {formatPrice(row.close)}
                    </td>
                    <td className="px-4 py-2.5 font-mono">
                      {formatPrice(row.ma_7d)}
                    </td>
                    <td className="px-4 py-2.5 font-mono">
                      {formatPrice(row.ma_30d)}
                    </td>
                    <td
                      className={`px-4 py-2.5 font-mono sm:px-6 ${
                        (row.daily_return_pct ?? 0) >= 0
                          ? "text-[var(--up)]"
                          : "text-[var(--down)]"
                      }`}
                    >
                      {formatPct(row.daily_return_pct)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

    </div>
  );
}

function Stat({
  label,
  value,
  tone,
  info,
}: {
  label: string;
  value: string;
  tone?: "up" | "down";
  info?: string;
}) {
  const valueClass =
    tone === "up"
      ? "text-[var(--up)]"
      : tone === "down"
        ? "text-[var(--down)]"
        : "text-[var(--ink)]";

  return (
    <div className="relative rounded-xl border border-[var(--line)] bg-[var(--panel)] px-4 py-4">
      {info ? (
        <div className="group absolute right-3 top-3">
          <button
            type="button"
            aria-label={`About ${label}`}
            className="flex h-5 w-5 items-center justify-center rounded-full border border-[var(--line)] font-mono text-[10px] text-[var(--muted)] hover:border-[var(--accent)] hover:text-[var(--ink)]"
          >
            i
          </button>
          <div
            role="tooltip"
            className="pointer-events-none absolute right-0 top-7 z-20 hidden w-56 rounded-lg border border-[var(--line)] bg-[var(--panel-strong)] px-3 py-2 text-left text-xs leading-relaxed text-[var(--muted)] shadow-lg group-hover:block group-focus-within:block"
          >
            {info}
          </div>
        </div>
      ) : null}
      <p className="pr-6 font-mono text-[10px] uppercase tracking-[0.18em] text-[var(--muted)]">
        {label}
      </p>
      <p className={`mt-2 font-mono text-2xl ${valueClass}`}>{value}</p>
    </div>
  );
}
