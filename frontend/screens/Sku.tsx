import Link from "next/link";
import { notFound } from "next/navigation";
import { ForecastChart } from "@/components/ForecastChart";
import { Icon } from "@/components/Icon";
import { ImportPanel } from "@/components/ImportPanel";
import { findSkuIn, formatQty, formatSigned, metaFrom, modelFrom } from "@/data/catalog";
import { readWorkspace } from "@/data/workspace";

export function SkuScreen({ code }: { code: string }) {
  const bundle = readWorkspace();
  if (!bundle) return <ImportPanel />;
  const sku = findSkuIn(bundle, decodeURIComponent(code));
  if (!sku) notFound();
  const meta = metaFrom(bundle);
  const model = modelFrom(bundle);

  const waterfall = sku.steps.map((step) => ({
    label: step.label,
    value:
      step.delta !== undefined
        ? formatSigned(step.delta)
        : `${formatQty(step.value ?? 0)} ${sku.unit}`,
  }));

  return (
    <>
      <section className="card pad stack">
        <nav aria-label="Хлебные крошки" className="crumbs">
          <Link href="/">Склад</Link>
          <Icon name="chevron_right" />
          <Link href="/orders">Заказы</Link>
          <Icon name="chevron_right" />
          <span className="article">{sku.article}</span>
        </nav>
        <header className="head">
          <div>
            <h1>{sku.name}</h1>
            <p className="lede">
              {sku.code} · {sku.unit} · MOQ {sku.moq} · {sku.category} · {meta.supplier}
            </p>
          </div>
          <Link href="/orders" className="btn btn-primary">
            К заказу
          </Link>
        </header>
        <ul className="facts">
          {[
            ["Остаток", `${sku.stock} ${sku.unit}`],
            ["В пути", `${sku.inTransit} ${sku.unit}`],
            ["Прогноз модели", formatQty(sku.demandMonth)],
            ["Рекомендация", `${sku.recommended} ${sku.unit}`],
          ].map(([k, v]) => (
            <li key={k}>
              <p className="caps">{k}</p>
              <strong>{v}</strong>
            </li>
          ))}
        </ul>
      </section>

      <ForecastChart asOf={meta.asOf} series={bundle.series} supplier={meta.supplier} />

      <section className="split">
        <article className="card pad">
          <h2>Водопад по этой позиции</h2>
          <ol className="waterfall">
            {waterfall.map((step, i) => (
              <li key={step.label}>
                <span>
                  <span className="num">{i + 1}</span>
                  {step.label}
                </span>
                <strong>{step.value}</strong>
              </li>
            ))}
          </ol>
        </article>
        <article className="card pad stack">
          <h2>Обоснование</h2>
          <p className="muted">
            {formatQty(sku.recommended)} {sku.unit} — это не сам прогноз. {model.label} дал{" "}
            {formatQty(sku.demandMonth)} {sku.unit} на следующий месяц, дальше {model.policy}.
            История с наличием: {sku.monthsUsed} мес.
            {sku.stockout12m > 0
              ? ` ${sku.stockout12m} мес. дефицита за год модель видит как stockout, а не как «спроса не было».`
              : ""}
            {sku.inTransit > 0 ? ` В пути уже ${formatQty(sku.inTransit)}${sku.inTransitEta ? ` (${sku.inTransitEta})` : ""}.` : ""}
          </p>
          {sku.lostDemand > 0 ? (
            <p className="warn">
              Упущено за 12 мес. из-за отсутствия товара: ≈{formatQty(sku.lostDemand)} {sku.unit}.
              В заказ не добавляется — это оценка потерь, а не потребность.
            </p>
          ) : null}
          {sku.neverStocked || sku.noStockRecord || sku.monthsUsed < 3 ? (
            <p className="hint">
              Рекомендация слабо обоснована: истории наличия на складе почти
              нет ({sku.monthsUsed} мес.). Проверьте позицию вручную.
            </p>
          ) : null}
        </article>
      </section>
    </>
  );
}
