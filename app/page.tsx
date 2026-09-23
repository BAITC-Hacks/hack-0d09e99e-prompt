import Link from "next/link";
import { ForecastChart } from "./components/ForecastChart";
import { Icon } from "./components/Icon";
import { KpiCard } from "./components/KpiCard";
import { StatusBadge } from "./components/StatusBadge";
import { alerts, categories, formatQty, kpis } from "./data/catalog";

export default function DashboardPage() {
  return (
    <div className="flex flex-col gap-6">
      <section className="card flex flex-col justify-between gap-4 p-4 xl:flex-row xl:items-center">
        <header>
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-2xl font-semibold tracking-tight text-ink">Обзор запасов и прогноз спроса</h1>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-status-safe-bg px-2.5 py-0.5 text-[11px] font-semibold text-status-safe">
              Выгрузка 1С · 22.09.2026
            </span>
          </div>
          <p className="mt-1 text-[13px] text-ink-secondary">
            Qor · склад Алматы · поставщик IEK · {kpis.skuTotal} SKU в помесячных продажах
          </p>
        </header>
        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center gap-1 rounded-lg bg-surface-low px-3 py-1.5 text-[13px]">
            <Icon name="warehouse" className="text-base text-primary-container" />
            Склад: <strong>Алматы</strong>
          </span>
          <span className="inline-flex items-center gap-1 rounded-lg bg-surface-low px-3 py-1.5 text-[13px]">
            <Icon name="date_range" className="text-base text-secondary" />
            Горизонт: <strong>8 недель</strong>
          </span>
          <Link href="/orders" className="inline-flex items-center gap-1 rounded-lg bg-primary-container px-3 py-2 text-[13px] font-medium text-white shadow-sm">
            <Icon name="bolt" className="text-lg" />
            К заказам ({kpis.toOrder})
          </Link>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4" aria-label="Ключевые показатели">
        <KpiCard label="Позиций к заказу" value={String(kpis.toOrder)} unit="SKU" hint="need = прогноз − остаток − в пути" accent="bg-primary-container" icon="shopping_cart_checkout" />
        <KpiCard label="Риск дефицита" value={String(kpis.deficit)} unit="SKU" hint="Пустой остаток на сент. 2026" accent="bg-status-critical" icon="warning" chip={`Критично: ${kpis.critical}`} chipClass="bg-status-critical-bg text-status-critical" valueClass="text-status-critical" />
        <KpiCard label="Излишки" value={String(kpis.excess)} unit="SKU" hint="Остаток > 6 мес. спроса" accent="bg-status-warning" icon="inventory_2" />
        <KpiCard label="В пути" value={formatQty(kpis.inboundQty)} unit="шт" hint={`${kpis.inboundSku} SKU в 6 входящих УТ`} accent="bg-secondary" icon="local_shipping" />
      </section>

      <aside className="card relative overflow-hidden p-4">
        <div className="absolute bottom-0 left-0 top-0 w-1.5 bg-ai-insight" />
        <div className="flex flex-col justify-between gap-3 pl-3 md:flex-row md:items-center">
          <div>
            <p className="flex flex-wrap items-center gap-2 text-[13px] font-semibold text-ink">
              Рекомендация по выгрузке IEK
              <span className="rounded bg-ai-insight-bg px-2 py-0.5 text-[11px] font-medium text-ai-insight">сезонность октября 1.24</span>
            </p>
            <p className="text-xs text-ink-secondary">
              {kpis.toOrder} позиций к заказу, {kpis.critical} критичных. В пути {formatQty(kpis.inboundQty)} ед. по 300 артикулам. Цен в выгрузке нет — считаем штуки.
            </p>
          </div>
          <Link href="/orders" className="rounded-lg bg-primary-container px-3 py-1.5 text-[13px] font-medium text-white">
            Открыть заказы
          </Link>
        </div>
      </aside>

      <section className="grid grid-cols-1 items-start gap-4 lg:grid-cols-12">
        <ForecastChart />
        <article className="card flex flex-col gap-4 p-4 lg:col-span-4">
          <header>
            <h2 className="text-xl font-semibold text-ink">Категории (по наименованию)</h2>
            <p className="text-xs text-ink-secondary">Доля SKU к заказу. Отдельного справочника категорий в 1С нет.</p>
          </header>
          <ol className="flex flex-col gap-4">
            {categories.map((cat, i) => (
              <li key={cat.name}>
                <div className="flex items-center justify-between text-[13px]">
                  <span className="font-medium text-ink">
                    {i + 1}. {cat.name}
                  </span>
                  <span className="font-semibold">
                    {cat.toOrder} <span className="text-xs font-normal text-ink-muted">({cat.share}%)</span>
                  </span>
                </div>
                <div className="mt-1 h-2 overflow-hidden rounded-full bg-surface-high">
                  <div className={`h-full rounded-full ${i === 0 ? "bg-primary" : i === 1 ? "bg-secondary-container" : i === 2 ? "bg-ai-insight" : "bg-[#636e83]"}`} style={{ width: `${cat.share}%` }} />
                </div>
                <p className="mt-1 text-xs text-ink-secondary">
                  {cat.sku} SKU · пустой остаток: {cat.empty}
                </p>
              </li>
            ))}
          </ol>
        </article>
      </section>

      <section className="card overflow-hidden">
        <header className="flex flex-col justify-between gap-3 p-4 sm:flex-row sm:items-center">
          <div>
            <h2 className="text-xl font-semibold text-ink">Критичные позиции</h2>
            <p className="text-xs text-ink-secondary">Пустой остаток или запас короче горизонта поставки</p>
          </div>
          <Link href="/orders" className="rounded-lg bg-status-critical-bg px-3 py-1.5 text-[13px] font-semibold text-status-critical">
            Все заказы
          </Link>
        </header>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-[13px]">
            <thead>
              <tr className="bg-surface-low text-[11px] font-semibold uppercase tracking-wider text-ink-secondary">
                <th className="px-4 py-2.5">Артикул / наименование</th>
                <th className="px-4 py-2.5 text-right">Остаток</th>
                <th className="px-4 py-2.5 text-center">В пути</th>
                <th className="px-4 py-2.5 text-right">Рек. заказ</th>
                <th className="px-4 py-2.5 text-center">Статус</th>
              </tr>
            </thead>
            <tbody>
              {alerts.map((row) => (
                <tr key={row.code} className="border-t border-line/70 hover:bg-surface-low/70">
                  <td className="px-4 py-3">
                    <Link href={`/sku/${encodeURIComponent(row.article)}`} className="font-semibold text-ink hover:text-primary-container">
                      {row.name}
                    </Link>
                    <p className="mono-sku text-ink-muted">
                      {row.article} · {row.code}
                    </p>
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    {row.stock} {row.unit}
                  </td>
                  <td className="px-4 py-3 text-center">{row.inTransit || "—"}</td>
                  <td className="px-4 py-3 text-right font-medium">
                    {row.recommended} {row.unit}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <StatusBadge tone={row.urgency} pulse />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
