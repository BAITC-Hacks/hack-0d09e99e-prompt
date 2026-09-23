import Link from "next/link";
import { ForecastChart } from "../../components/ForecastChart";
import { Icon } from "../../components/Icon";
import { findSku, formatQty } from "../../data/catalog";

export default async function SkuPage({ params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  const sku = findSku(code);
  const waterfall = [
    { label: "Спрос/мес после IQR", value: `${formatQty(sku.demandMonth)} ${sku.unit}` },
    { label: "Сезонность октября 1.24 × 8 недель", value: `${formatQty(sku.forecast8w)} ${sku.unit}` },
    { label: "Компенсация пустого остатка", value: `+${formatQty(sku.lostDemand)}` },
    { label: "Текущий остаток", value: `−${formatQty(sku.stock)}` },
    { label: "В пути", value: `−${formatQty(sku.inTransit)}` },
    { label: "Округление до MOQ", value: `${sku.recommended} ${sku.unit}` },
  ];

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
              {sku.code} · {sku.unit} · MOQ {sku.moq} · {sku.category} · IEK · Алматы
            </p>
          </div>
          <Link href="/orders" className="rounded-lg bg-primary px-3 py-2 text-[13px] font-medium text-white">
            К заказу IEK
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

      <ForecastChart />

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
            {sku.recommended} {sku.unit}: медианный спрос после отсечения выбросов, умноженный на коэффициент октября из файла сезонности.
            {sku.stockoutNow ? " Остаток в сентябре пустой — добавлена компенсация упущенного спроса." : ""}
            {sku.inTransit > 0 ? ` В пути уже ${formatQty(sku.inTransit)} (${sku.inTransitEta}).` : ""}
          </p>
        </article>
      </section>
    </div>
  );
}
