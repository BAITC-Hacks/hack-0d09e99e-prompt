import Link from "next/link";
import { notFound } from "next/navigation";
import { ForecastChart } from "../../components/ForecastChart";
import { Icon } from "../../components/Icon";
import { ImportPanel } from "../../components/ImportPanel";
import { findSkuIn, formatQty, formatSigned, metaFrom } from "../../data/catalog";
import { readWorkspace } from "../../data/workspace";

export default async function SkuPage({ params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  const bundle = readWorkspace();
  if (!bundle) return <ImportPanel />;
  const sku = findSkuIn(bundle, decodeURIComponent(code));
  if (!sku) notFound();
  const meta = metaFrom(bundle);

  // Шаги приходят из движка. Здесь только форматирование — формулы тут нет.
  const waterfall = sku.steps.map((step) => ({
    label: step.label,
    value:
      step.delta !== undefined
        ? formatSigned(step.delta)
        : `${formatQty(step.value ?? 0)} ${sku.unit}`,
  }));

  return (
    <div className="flex flex-col gap-6">
      <section className="card space-y-3 p-4">
        <nav aria-label="Хлебные крошки" className="flex items-center gap-1 text-xs text-ink-secondary">
          <Link href="/" className="hover:text-primary-container">Склад</Link>
          <Icon name="chevron_right" className="text-sm" />
          <Link href="/orders" className="hover:text-primary-container">Заказы</Link>
          <Icon name="chevron_right" className="text-sm" />
          <span className="mono-sku font-semibold text-primary-container">{sku.article}</span>
        </nav>
        <header className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-ink">{sku.name}</h1>
            <p className="mt-1 text-[13px] text-ink-secondary">
              {sku.code} · {sku.unit} · MOQ {sku.moq} · {sku.category} · {meta.supplier} · {meta.warehouse}
            </p>
          </div>
          <Link href="/orders" className="rounded-lg bg-primary px-3 py-2 text-[13px] font-medium text-white">
            К заказу
          </Link>
        </header>
        <ul className="grid grid-cols-2 gap-2 md:grid-cols-4">
          {[
            ["Остаток", `${sku.stock} ${sku.unit}`],
            ["В пути", `${sku.inTransit} ${sku.unit}`],
            ["Спрос / мес", formatQty(sku.demandMonth)],
            ["Рекомендация", `${sku.recommended} ${sku.unit}`],
          ].map(([k, v]) => (
            <li key={k} className="rounded-xl border border-line bg-surface-low/50 p-3">
              <p className="label-caps">{k}</p>
              <p className="mt-1 text-xl font-semibold">{v}</p>
            </li>
          ))}
        </ul>
      </section>

      <ForecastChart asOf={meta.asOf} series={bundle.series} supplier={meta.supplier} />

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        <article className="card p-4 lg:col-span-8">
          <h2 className="mb-3 text-xl font-semibold text-ink">Водопад по этой позиции</h2>
          <ol className="space-y-2">
            {waterfall.map((step, i) => (
              <li key={step.label} className="flex items-center justify-between gap-3 rounded-lg border border-line px-3 py-2.5">
                <span className="flex items-center gap-2 text-[13px]">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-surface-low text-[11px] font-semibold">{i + 1}</span>
                  {step.label}
                </span>
                <strong className="tabular-nums text-[13px]">{step.value}</strong>
              </li>
            ))}
          </ol>
        </article>
        <article className="card p-4 lg:col-span-4">
          <h2 className="text-xl font-semibold">Обоснование</h2>
          <p className="mt-2 text-[13px] text-ink-secondary">
            {formatQty(sku.recommended)} {sku.unit}: медианный спрос{" "}
            {formatQty(sku.demandMonth)} {sku.unit}/мес, посчитанный по {sku.monthsUsed} мес.
            с наличием на складе, на горизонт {meta.horizonWeeks} нед. с учётом сезонности
            (×{meta.monthEquiv}).
            {sku.stockout12m > 0
              ? ` Месяцы дефицита (${sku.stockout12m} за последние 12) из оценки исключены — иначе спрос занижается.`
              : ""}
            {sku.inTransit > 0 ? ` В пути уже ${formatQty(sku.inTransit)} (${sku.inTransitEta}).` : ""}
          </p>
          {sku.lostDemand > 0 ? (
            <p className="mt-2 rounded-lg border border-status-warning-border bg-status-warning-bg p-2 text-xs text-status-warning">
              Упущено за 12 мес. из-за отсутствия товара: ≈{formatQty(sku.lostDemand)} {sku.unit}.
              В заказ не добавляется — это оценка потерь, а не потребность.
            </p>
          ) : null}
          {sku.neverStocked || sku.noStockRecord || sku.monthsUsed < 3 ? (
            <p className="mt-2 rounded-lg border border-line bg-surface-low p-2 text-xs text-ink-secondary">
              Рекомендация слабо обоснована: истории наличия на складе {meta.warehouse} почти
              нет ({sku.monthsUsed} мес.). Проверьте позицию вручную.
            </p>
          ) : null}
        </article>
      </section>
    </div>
  );
}
