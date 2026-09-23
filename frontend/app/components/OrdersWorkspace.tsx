"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { formatQty, formatSigned, metaFrom, type OrderLine } from "@/app/data/catalog";
import { Icon } from "./Icon";
import { ImportPanel } from "./ImportPanel";
import { StatusBadge } from "./StatusBadge";
import { useWorkspace } from "./WorkspaceProvider";

/** Количество допустимо, если это целое ≥ 0 и кратно минимальной партии. */
function isValidQty(raw: string, moq: number) {
  if (raw.trim() === "") return false;
  const n = Number(raw);
  if (!Number.isInteger(n) || n < 0) return false;
  return moq <= 1 || n % moq === 0;
}

export function OrdersWorkspace() {
  const { bundle } = useWorkspace();
  const lines = bundle?.lines ?? [];
  const kpis = bundle?.kpis;
  const anomalies = bundle?.anomalies ?? [];
  const meta = bundle ? metaFrom(bundle) : null;
  const [query, setQuery] = useState("");
  const [tone, setTone] = useState<"all" | "critical" | "warning">("critical");
  const [openRow, setOpenRow] = useState(lines[0]?.code ?? "");
  // Сырой текст поля, а не число: иначе очистка ввода схлопывает количество в 0.
  const [qty, setQty] = useState<Record<string, string>>({});
  const [limit, setLimit] = useState(60);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return lines.filter((l) => {
      if (tone !== "all" && l.urgency !== tone) return false;
      if (!q) return true;
      return `${l.article} ${l.code} ${l.name}`.toLowerCase().includes(q);
    });
  }, [lines, query, tone]);

  const view = filtered.slice(0, limit);

  // Заказ уходит в 1С — количество обязано быть кратно минимальной партии.
  const invalid = useMemo(
    () =>
      Object.entries(qty)
        .map(([code, raw]) => ({ line: lines.find((l) => l.code === code), raw }))
        .filter(({ line, raw }) => line && !isValidQty(raw, line.moq)),
    [lines, qty],
  );

  if (!bundle || !kpis || !meta) return <ImportPanel />;

  return (
    <div className="flex flex-col gap-4">
      <header className="flex flex-col justify-between gap-3 xl:flex-row xl:items-center">
        <div>
          <p className="label-caps text-ink-muted">Qor / Заказы поставщикам</p>
          <h1 className="text-[30px] font-bold tracking-tight text-ink">Рекомендованные заказы</h1>
          <p className="mt-1 text-xs text-ink-secondary">
            {meta.warehouse} · {meta.supplier} · {meta.horizonWeeks} недель · выгрузка {meta.asOfLabel} · без цен
          </p>
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
          <button
            type="button"
            disabled={invalid.length > 0}
            title={invalid.length > 0 ? "Есть количества не кратные MOQ" : undefined}
            className="rounded-lg bg-primary px-3 py-1.5 text-[13px] font-medium text-white disabled:cursor-not-allowed disabled:bg-ink-muted"
          >
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
          {invalid.length > 0 ? (
            <span className="ml-2 font-medium text-status-critical">
              · {invalid.length} поз. с количеством не кратным MOQ — согласование заблокировано
            </span>
          ) : null}
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
                    qty={qty[line.code] ?? String(line.recommended)}
                    open={openRow === line.code}
                    onQty={(v) => setQty((s) => ({ ...s, [line.code]: v }))}
                    onToggle={() => setOpenRow((cur) => (cur === line.code ? "" : line.code))}
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
  qty: string;
  open: boolean;
  onQty: (v: string) => void;
  onToggle: () => void;
}) {
  const valid = isValidQty(qty, line.moq);
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
          <input
            type="number"
            min={0}
            step={line.moq > 1 ? line.moq : 1}
            value={qty}
            onChange={(e) => onQty(e.target.value)}
            aria-invalid={!valid}
            aria-label={`Количество, ${line.article}`}
            title={valid ? undefined : `Кратно ${line.moq} (MOQ)`}
            className={`w-16 rounded-md border px-1 py-1 text-right text-xs font-semibold ${
              valid ? "border-primary" : "border-status-critical bg-status-critical-bg text-status-critical"
            }`}
          />
          {!valid ? (
            <p className="mt-0.5 text-[10px] font-medium text-status-critical">кратно {line.moq}</p>
          ) : null}
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
            <p className="text-sm font-semibold text-ink">
              Почему {formatQty(line.recommended)} {line.unit}
            </p>
            {/* Шаги приходят из движка — формулы в вёрстке нет. */}
            <ul className="mt-2 grid grid-cols-2 gap-2 lg:grid-cols-5">
              {line.steps.map((step) => (
                <li key={step.key} className="rounded-lg border border-line p-2 text-xs">
                  {step.label}
                  <strong className="block tabular-nums">
                    {step.delta !== undefined ? formatSigned(step.delta) : formatQty(step.value ?? 0)}
                  </strong>
                </li>
              ))}
            </ul>
            <p className="mt-2 text-[11px] text-ink-secondary">
              Спрос оценён по {line.monthsUsed} мес. с наличием на складе
              {line.stockout12m > 0 ? `; ${line.stockout12m} мес. дефицита за год исключены` : ""}.
              {line.lostDemand > 0
                ? ` Упущено ≈${formatQty(line.lostDemand)} ${line.unit} — в заказ не входит.`
                : ""}
            </p>
          </td>
        </tr>
      ) : null}
    </>
  );
}
