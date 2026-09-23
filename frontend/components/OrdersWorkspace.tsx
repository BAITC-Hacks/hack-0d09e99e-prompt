"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { formatQty, formatSigned, metaFrom, type OrderLine } from "@/data/catalog";
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
    <>
      <header className="head">
        <div>
          <p className="caps">Qor / Заказы поставщикам</p>
          <h1>Рекомендованные заказы</h1>
          <p className="lede">
            {meta.warehouse} · {meta.supplier} · {meta.horizonWeeks} недель · выгрузка {meta.asOfLabel} · без цен
          </p>
        </div>
        <div className="actions">
          <span className="chip">
            К заказу: <strong>{kpis.toOrder} SKU</strong>
          </span>
          <span className="chip-critical">Критично: {kpis.critical}</span>
          <button type="button" disabled className="btn">
            Экспорт в 1С
          </button>
          <button
            type="button"
            disabled={invalid.length > 0}
            title={invalid.length > 0 ? "Есть количества не кратные MOQ" : undefined}
            className="btn btn-primary"
          >
            Отправить на согласование
          </button>
        </div>
      </header>

      <section className="card pad stack" aria-label="Фильтры">
        <div className="filters">
          <label className="search">
            <span className="skip">Поиск</span>
            <Icon name="search" />
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Артикул, код 1С, наименование" />
          </label>
          <select value={tone} onChange={(e) => setTone(e.target.value as typeof tone)}>
            <option value="critical">Срочность: критично ({kpis.critical})</option>
            <option value="warning">Скоро</option>
            <option value="all">Все {kpis.toOrder}</option>
          </select>
          <Link href="/anomalies" className="chip-insight">
            Аномалии ({anomalies.length})
          </Link>
        </div>
        <p className="muted">
          Показано <strong>{view.length}</strong> из {filtered.length}
          {invalid.length > 0 ? (
            <span className="error">
              {" "}
              · {invalid.length} поз. с количеством не кратным MOQ — согласование заблокировано
            </span>
          ) : null}
        </p>
      </section>

      <div className="split">
        <section className="card">
          <header className="pad head">
            <h2>{meta.supplier}</h2>
            <span className="muted">в пути {formatQty(kpis.inboundQty)} ед. · {kpis.inboundSku} SKU</span>
          </header>
          <div className="scroll">
            <table>
              <thead>
                <tr>
                  <th>Артикул</th>
                  <th>Остаток</th>
                  <th>В пути</th>
                  <th>Спрос/мес</th>
                  <th>Прогноз 8н</th>
                  <th>Рек.</th>
                  <th>Статус</th>
                  <th />
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
            <button type="button" onClick={() => setLimit((n) => n + 80)} className="more">
              Ещё {filtered.length - limit}
            </button>
          ) : null}
        </section>

        <aside className="card pad summary">
          <h2>Сводка</h2>
          <dl>
            <div><dt className="muted">Поставщик</dt><dd>{meta.supplier}</dd></div>
            <div><dt className="muted">К заказу</dt><dd>{kpis.toOrder}</dd></div>
            <div><dt className="muted">Критично</dt><dd>{kpis.critical}</dd></div>
            <div><dt className="muted">Статус</dt><dd>Черновик</dd></div>
          </dl>
          <p className="warn">Заказ не уходит поставщику. После согласования — экспорт в 1С.</p>
        </aside>
      </div>
    </>
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
      <tr data-open={open ? "true" : undefined}>
        <td>
          <Link href={`/sku/${encodeURIComponent(line.article)}`} className="article">
            {line.article}
          </Link>
          <p>{line.name}</p>
          <p className="faint">
            {line.code} · MOQ {line.moq}
          </p>
        </td>
        <td className={line.stockoutNow ? "stockout" : undefined}>
          {line.stock} {line.unit}
        </td>
        <td>
          {line.inTransit || 0}
          {line.inTransitEta ? <p className="faint">{line.inTransitEta}</p> : null}
        </td>
        <td>{formatQty(line.demandMonth)}</td>
        <td>{formatQty(line.forecast8w)}</td>
        <td>
          <input
            type="number"
            min={0}
            step={line.moq > 1 ? line.moq : 1}
            value={qty}
            onChange={(e) => onQty(e.target.value)}
            aria-invalid={!valid}
            aria-label={`Количество, ${line.article}`}
            title={valid ? undefined : `Кратно ${line.moq} (MOQ)`}
            className="qty"
          />
          {!valid ? <p className="invalid">кратно {line.moq}</p> : null}
        </td>
        <td>
          <StatusBadge tone={line.urgency} pulse={line.urgency === "critical"} />
        </td>
        <td>
          <button type="button" onClick={onToggle} className="expand" aria-expanded={open}>
            <Icon name="auto_awesome" />
          </button>
        </td>
      </tr>
      {open ? (
        <tr>
          <td colSpan={8}>
            <p>
              <strong>
                Почему {formatQty(line.recommended)} {line.unit}
              </strong>
            </p>
            <ul className="steps">
              {line.steps.map((step) => (
                <li key={step.key}>
                  {step.label}
                  <strong>
                    {step.delta !== undefined ? formatSigned(step.delta) : formatQty(step.value ?? 0)}
                  </strong>
                </li>
              ))}
            </ul>
            <p className="muted">
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
