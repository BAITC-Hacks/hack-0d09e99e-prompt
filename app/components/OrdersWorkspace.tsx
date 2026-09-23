"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { anomalies, formatQty, kpis, lines, type OrderLine } from "@/app/data/catalog";
import { Icon } from "./Icon";
import { StatusBadge } from "./StatusBadge";

export function OrdersWorkspace() {
  const [query, setQuery] = useState("");
  const [tone, setTone] = useState<"all" | "critical" | "warning">("critical");
  const [openRow, setOpenRow] = useState(lines[0]?.article ?? "");
  const [qty, setQty] = useState<Record<string, number>>({});
  const [limit, setLimit] = useState(60);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return lines.filter((l) => {
      if (tone !== "all" && l.urgency !== tone) return false;
      if (!q) return true;
      return `${l.article} ${l.code} ${l.name}`.toLowerCase().includes(q);
    });
  }, [query, tone]);

  const view = filtered.slice(0, limit);

  return (
    <div className="flex flex-col gap-4">
      <header className="flex flex-col justify-between gap-3 xl:flex-row xl:items-center">
        <div>
          <p className="label-caps text-ink-muted">Qor / Заказы поставщикам</p>
          <h1 className="text-[30px] font-bold tracking-tight text-ink">Рекомендованные заказы</h1>
          <p className="mt-1 text-xs text-ink-secondary">Алматы · IEK · 8 недель · выгрузка 22.09.2026 · без цен</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-lg border border-line bg-card px-3 py-1.5 text-[13px] shadow-card">
            К заказу: <strong>{kpis.toOrder} SKU</strong>
          </span>
          <span className="rounded-lg border border-status-critical-border bg-status-critical-bg px-3 py-1.5 text-[11px] font-medium text-status-critical">
            Критично: {kpis.critical}
          </span>
          <button type="button" disabled className="rounded-lg border border-line px-3 py-1.5 text-[13px] text-ink-muted">
            Экспорт в 1С
          </button>
          <button type="button" className="rounded-lg bg-primary px-3 py-1.5 text-[13px] font-medium text-white">
            Отправить на согласование
          </button>
        </div>
      </header>

      <section className="card flex flex-col gap-3 p-3" aria-label="Фильтры">
        <div className="grid grid-cols-1 gap-2 md:grid-cols-12">
          <label className="relative md:col-span-6">
            <span className="sr-only">Поиск</span>
            <Icon name="search" className="absolute left-3 top-1/2 -translate-y-1/2 text-lg text-ink-muted" />
            <input value={query} onChange={(e) => setQuery(e.target.value)} className="w-full rounded-lg border border-line bg-surface-low py-1.5 pl-9 pr-3 text-[13px]" placeholder="Артикул, код 1С, наименование" />
          </label>
          <select className="rounded-lg border border-line px-3 py-1.5 text-xs md:col-span-3" value={tone} onChange={(e) => setTone(e.target.value as typeof tone)}>
            <option value="critical">Срочность: критично ({kpis.critical})</option>
            <option value="warning">Скоро</option>
            <option value="all">Все {kpis.toOrder}</option>
          </select>
          <Link href="/anomalies" className="inline-flex items-center justify-center rounded-lg border border-ai-insight-border bg-ai-insight-bg px-3 py-1.5 text-xs font-medium text-ai-insight md:col-span-3">
            Аномалии ({anomalies.length})
          </Link>
        </div>
        <p className="text-xs text-ink-secondary">
          Показано <strong className="text-ink">{view.length}</strong> из {filtered.length}
        </p>
      </section>

      <div className="grid grid-cols-1 items-start gap-4 lg:grid-cols-12">
        <section className="card overflow-hidden lg:col-span-8 xl:col-span-9">
          <header className="flex flex-wrap items-center justify-between gap-2 border-b border-line bg-surface-low/70 px-3 py-2">
            <h2 className="text-base font-semibold text-ink">IEK</h2>
            <span className="text-xs text-ink-secondary">в пути {formatQty(kpis.inboundQty)} ед. · {kpis.inboundSku} SKU</span>
          </header>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-left text-[13px]">
              <thead>
                <tr className="border-b border-line bg-surface-low/40 text-[11px] font-semibold uppercase tracking-wider text-ink-secondary">
                  <th className="px-3 py-2.5">Артикул</th>
                  <th className="px-3 py-2.5 text-right">Остаток</th>
                  <th className="px-3 py-2.5 text-right">В пути</th>
                  <th className="px-3 py-2.5 text-right">Спрос/мес</th>
                  <th className="px-3 py-2.5 text-right">Прогноз 8н</th>
                  <th className="px-3 py-2.5 text-right">Рек.</th>
                  <th className="px-3 py-2.5 text-center">Статус</th>
                  <th className="w-10 px-3 py-2.5" />
                </tr>
              </thead>
              <tbody>
                {view.map((line) => (
                  <OrderRows
                    key={line.code}
                    line={line}
                    qty={qty[line.code] ?? line.recommended}
                    open={openRow === line.article}
                    onQty={(v) => setQty((s) => ({ ...s, [line.code]: v }))}
                    onToggle={() => setOpenRow((cur) => (cur === line.article ? "" : line.article))}
                  />
                ))}
              </tbody>
            </table>
          </div>
          {filtered.length > limit ? (
            <button type="button" onClick={() => setLimit((n) => n + 80)} className="w-full border-t border-line py-2 text-sm text-primary-container">
              Ещё {filtered.length - limit}
            </button>
          ) : null}
        </section>

        <aside className="card sticky top-24 space-y-3 p-4 lg:col-span-4 xl:col-span-3">
          <h2 className="text-base font-semibold">Сводка</h2>
          <dl className="space-y-2 text-[13px]">
            <div className="flex justify-between"><dt className="text-ink-secondary">Поставщик</dt><dd>IEK</dd></div>
            <div className="flex justify-between"><dt className="text-ink-secondary">К заказу</dt><dd>{kpis.toOrder}</dd></div>
            <div className="flex justify-between"><dt className="text-ink-secondary">Критично</dt><dd>{kpis.critical}</dd></div>
            <div className="flex justify-between"><dt className="text-ink-secondary">Статус</dt><dd>Черновик</dd></div>
          </dl>
          <p className="rounded-lg border border-status-warning-border bg-status-warning-bg p-3 text-xs text-status-warning">
            Заказ не уходит поставщику. После согласования — экспорт в 1С.
          </p>
        </aside>
      </div>
    </div>
  );
}

function OrderRows({
  line,
  qty,
  open,
  onQty,
  onToggle,
}: {
  line: OrderLine;
  qty: number;
  open: boolean;
  onQty: (v: number) => void;
  onToggle: () => void;
}) {
  return (
    <>
      <tr className={`border-t border-line/70 ${open ? "border-l-4 border-l-primary bg-primary/5" : "hover:bg-surface-low/70"}`}>
        <td className="px-3 py-2.5">
          <Link href={`/sku/${encodeURIComponent(line.article)}`} className="mono-sku font-semibold text-primary-container">
            {line.article}
          </Link>
          <p className="max-w-xs font-medium leading-snug text-ink">{line.name}</p>
          <p className="text-[11px] text-ink-muted">
            {line.code} · MOQ {line.moq}
          </p>
        </td>
        <td className={`px-3 py-2.5 text-right tabular-nums ${line.stockoutNow ? "font-semibold text-status-critical" : ""}`}>
          {line.stock} {line.unit}
        </td>
        <td className="px-3 py-2.5 text-right text-ink-secondary">
          {line.inTransit || 0}
          {line.inTransitEta ? <p className="text-[10px]">{line.inTransitEta}</p> : null}
        </td>
        <td className="px-3 py-2.5 text-right tabular-nums">{formatQty(line.demandMonth)}</td>
        <td className="px-3 py-2.5 text-right tabular-nums">{formatQty(line.forecast8w)}</td>
        <td className="px-3 py-2.5 text-right">
          <input type="number" min={0} value={qty} onChange={(e) => onQty(Number(e.target.value))} className="w-16 rounded-md border border-primary px-1 py-1 text-right text-xs font-semibold" />
        </td>
        <td className="px-3 py-2.5 text-center">
          <StatusBadge tone={line.urgency} pulse={line.urgency === "critical"} />
        </td>
        <td className="px-3 py-2.5 text-center">
          <button type="button" onClick={onToggle} className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-ai-insight-bg text-ai-insight" aria-expanded={open}>
            <Icon name="auto_awesome" className="text-base" />
          </button>
        </td>
      </tr>
      {open ? (
        <tr>
          <td colSpan={8} className="bg-card p-3">
            <p className="text-sm font-semibold text-ink">Почему {qty} {line.unit}</p>
            <ul className="mt-2 grid grid-cols-2 gap-2 lg:grid-cols-4">
              <li className="rounded-lg border border-line p-2 text-xs">
                Спрос/мес (IQR) <strong className="block">{formatQty(line.demandMonth)}</strong>
              </li>
              <li className="rounded-lg border border-line p-2 text-xs">
                × сезон окт. 1.24 × 2 мес. <strong className="block">{formatQty(line.forecast8w)}</strong>
              </li>
              <li className="rounded-lg border border-line p-2 text-xs">
                Stockout + <strong className="block">{formatQty(line.lostDemand)}</strong>
              </li>
              <li className="rounded-lg border border-line p-2 text-xs">
                − остаток − в пути, ceil MOQ <strong className="block">{line.recommended}</strong>
              </li>
            </ul>
          </td>
        </tr>
      ) : null}
    </>
  );
}
