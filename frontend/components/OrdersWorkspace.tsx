"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { cleanText, formatQty, formatSigned, metaFrom, modelFrom, supplierArticle, type OrderLine } from "@/data/catalog";
import { Icon } from "./Icon";
import { ImportPanel } from "./ImportPanel";
import { useSession } from "./SessionProvider";
import { StatusBadge } from "./StatusBadge";
import { useWorkspace } from "./WorkspaceProvider";

/** Количество допустимо, если это целое ≥ 0 и кратно минимальной партии. */
type OrderState = {
  status: "draft" | "pending_approval" | "approved" | "returned";
  sentBy?: string | null;
  decidedBy?: string | null;
  comment?: string | null;
};

const statusLabel: Record<OrderState["status"], string> = {
  draft: "Черновик",
  pending_approval: "На согласовании",
  approved: "Утверждено",
  returned: "На доработке",
};

function approvalHint(status: OrderState["status"], order: OrderState | null) {
  if (status === "pending_approval") {
    return `Отправлено${order?.sentBy ? ` (${order.sentBy})` : ""}. Руководитель утверждает или возвращает в приложении. Поставщику заказ не уходит.`;
  }
  if (status === "returned") {
    return order?.comment ? `Руководитель вернул: ${order.comment}` : "Руководитель вернул заказ на доработку.";
  }
  if (status === "approved") {
    return `Утверждено${order?.decidedBy ? ` (${order.decidedBy})` : ""}. Дальше — экспорт в 1С. Поставщику само не уходит.`;
  }
  return "Кнопка только переводит черновик в «на согласовании». В 1С и поставщику ничего не отправляется.";
}

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
  const model = bundle ? modelFrom(bundle) : null;
  const { user } = useSession();
  const [query, setQuery] = useState("");
  const [tone, setTone] = useState<"all" | "critical" | "warning">("critical");
  const [category, setCategory] = useState("all");
  const [withArticle, setWithArticle] = useState(false);
  const [openRow, setOpenRow] = useState("");
  const [order, setOrder] = useState<OrderState | null>(null);
  const [sending, setSending] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  // Сырой текст поля, а не число: иначе очистка ввода схлопывает количество в 0.
  const [qty, setQty] = useState<Record<string, string>>({});
  const [limit, setLimit] = useState(60);

  const categories = useMemo(() => [...new Set(lines.map((l) => l.category))].sort((a, b) => a.localeCompare(b, "ru")), [lines]);

  useEffect(() => {
    let cancel = false;
    fetch("/api/orders/current")
      .then(async (res) => {
        const data = await res.json();
        if (!cancel && res.ok) setOrder(data as OrderState);
      })
      .catch(() => undefined);
    return () => {
      cancel = true;
    };
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return lines.filter((l) => {
      if (tone !== "all" && l.urgency !== tone) return false;
      if (category !== "all" && l.category !== category) return false;
      if (withArticle && !supplierArticle(l)) return false;
      if (!q) return true;
      return `${l.article} ${l.code} ${cleanText(l.name)}`.toLowerCase().includes(q);
    });
  }, [lines, query, tone, category, withArticle]);

  const view = filtered.slice(0, limit);

  // Заказ уходит в 1С — количество обязано быть кратно минимальной партии.
  const invalid = useMemo(
    () =>
      Object.entries(qty)
        .map(([code, raw]) => ({ line: lines.find((l) => l.code === code), raw }))
        .filter(({ line, raw }) => line && !isValidQty(raw, line.moq)),
    [lines, qty],
  );

  const status = order?.status ?? "draft";
  const canSubmit = user?.role === "buyer" && (status === "draft" || status === "returned") && invalid.length === 0 && !sending;

  async function sendForApproval() {
    setSending(true);
    setSubmitError(null);
    try {
      const res = await fetch("/api/orders/submit", { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "не отправилось");
      setOrder(data as OrderState);
    } catch (e) {
      setSubmitError(e instanceof Error ? e.message : "не отправилось");
    } finally {
      setSending(false);
    }
  }

  if (!bundle || !kpis || !meta) return <ImportPanel />;

  return (
    <>
      <header className="head">
        <div>
          <p className="caps">Qor / Заказы поставщикам</p>
          <h1>Рекомендованные заказы</h1>
          <p className="lede">
            {meta.supplier} · {model?.label} · {model?.target} · выгрузка {meta.asOfLabel}
          </p>
        </div>
        <div className="actions">
          <span className="chip">
            К заказу: <strong>{kpis.toOrder} SKU</strong>
          </span>
          <button type="button" disabled className="btn" title="Экспорт в 1С откроется после утверждения руководителем">
            Экспорт в 1С
          </button>
          <button
            type="button"
            disabled={!canSubmit}
            title={
              user?.role === "director"
                ? "Отправляет менеджер закупа. Руководитель утверждает в приложении."
                : invalid.length > 0
                  ? "Есть количества не кратные MOQ"
                  : "Статус станет «на согласовании». Поставщику ничего не уйдёт."
            }
            className="btn btn-primary"
            onClick={() => void sendForApproval()}
          >
            {sending ? "Отправляем…" : status === "pending_approval" ? "На согласовании" : "Отправить на согласование"}
          </button>
        </div>
      </header>

      <section className="card pad stack" aria-label="Фильтры">
        <div className="filters">
          <label className="search">
            <span className="skip">Поиск</span>
            <Icon name="search" />
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Название, артикул IEK или код 1С" />
          </label>
          <select value={tone} onChange={(e) => setTone(e.target.value as typeof tone)}>
            <option value="critical">Срочность: критично ({kpis.critical})</option>
            <option value="warning">Скоро</option>
            <option value="all">Все {kpis.toOrder}</option>
          </select>
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="all">Все категории</option>
            {categories.map((name) => (
              <option key={name} value={name}>{name}</option>
            ))}
          </select>
          <Link href="/anomalies" className="chip-insight">
            Аномалии ({anomalies.length})
          </Link>
        </div>
        <label className="check">
          <input type="checkbox" checked={withArticle} onChange={(e) => setWithArticle(e.target.checked)} />
          Только с артикулом поставщика — без позиций, где в файле остался только код 1С
        </label>
        {submitError ? <p className="error">{submitError}</p> : null}
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
                  <th>Прогноз</th>
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
            <div><dt className="muted">Статус</dt><dd>{statusLabel[status]}</dd></div>
            {model ? <div><dt className="muted">Модель</dt><dd>{model.label}</dd></div> : null}
          </dl>
          {model ? <p className="muted">{model.policy}. Колонка «Прогноз» — это она, «Рек.» — уже заказ.</p> : null}
          <p className="warn">{approvalHint(status, order)}</p>
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
          <Link href={`/sku/${encodeURIComponent(line.article)}`} className="thing">
            {cleanText(line.name)}
          </Link>
          <p className="faint">
            {supplierArticle(line) ? <span className="article">{supplierArticle(line)} · </span> : null}
            код 1С {line.code} · {line.category} · MOQ {line.moq}
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
          <td colSpan={7}>
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
              Прогноз — CatBoost на следующий месяц, не среднее. История: {line.monthsUsed} мес. с наличием
              {line.stockout12m > 0 ? `; ${line.stockout12m} мес. дефицита учтены как stockout` : ""}.
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
