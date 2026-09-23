"use client";

import Link from "next/link";
import { ForecastChart } from "@/components/ForecastChart";
import { Icon } from "@/components/Icon";
import { ImportPanel } from "@/components/ImportPanel";
import { KpiCard } from "@/components/KpiCard";
import { StatusBadge } from "@/components/StatusBadge";
import { useWorkspace } from "@/components/WorkspaceProvider";
import { cleanText, formatQty, metaFrom, modelFrom, peakSeasonFrom, supplierArticle } from "@/data/catalog";

export function Dashboard() {
  const { bundle } = useWorkspace();
  if (!bundle) return <ImportPanel />;
  const { alerts, categories, kpis } = bundle;
  const meta = metaFrom(bundle);
  const model = modelFrom(bundle);
  const peakSeason = peakSeasonFrom(bundle);
  const hasSeries = bundle.series.length > 0;

  return (
    <>
      <section className="card pad head">
        <header>
          <div className="actions">
            <h1>Обзор запасов и прогноз спроса</h1>
            <span className="chip-safe">Выгрузка 1С · {meta.asOfLabel}</span>
          </div>
          <p className="lede">
            Стол менеджера закупа: что заказать и сколько. Цифру считает {model.label}, количество правится в заказах, утверждает руководитель в приложении.
          </p>
        </header>
        <div className="actions">
          <span className="chip-insight">
            <Icon name="psychology" />
            {model.label}: {model.target}
          </span>
          <Link href="/orders" className="btn btn-accent">
            <Icon name="bolt" />
            К заказам ({kpis.toOrder})
          </Link>
        </div>
      </section>

      <section className="metrics" aria-label="Ключевые показатели">
        <KpiCard label="Позиций к заказу" value={String(kpis.toOrder)} unit="SKU" hint={model.policy} icon="shopping_cart_checkout" />
        <KpiCard label="Риск дефицита" value={String(kpis.deficit)} unit="SKU" hint={`Пустой остаток на ${meta.asOfLabel}`} tone="critical" icon="warning" chip={`Критично: ${kpis.critical}`} />
        <KpiCard label="Излишки" value={String(kpis.excess)} unit="SKU" hint="Остаток > 6 мес. спроса" tone="warning" icon="inventory_2" />
        <KpiCard label="В пути" value={formatQty(kpis.inboundQty)} unit="шт" hint={`${kpis.inboundSku} SKU`} tone="secondary" icon="local_shipping" />
      </section>

      <aside className="card note model">
        <div className="head">
          <div>
            <p>
              {model.label} по выгрузке {meta.supplier}
              {peakSeason ? <span className="chip-insight">сезонность {peakSeason.month} {peakSeason.coef}</span> : null}
            </p>
            <p className="lede">
              Сначала модель даёт {model.target}. Затем правило заказа: {model.policy}. В таблице это колонка «Прогноз» и кнопка «почему».
            </p>
            <p className="muted">
              {kpis.toOrder} позиций к заказу, {kpis.critical} критичных. В пути {formatQty(kpis.inboundQty)} ед. по {kpis.inboundSku} артикулам. Цен в выгрузке нет — считаем штуки.
              {(kpis.unverified ?? 0) > 0 ? ` ${kpis.unverified} позиций без истории остатков вынесены из витрины.` : ""}
            </p>
          </div>
          <Link href="/orders" className="btn">К таблице заказов</Link>
        </div>
      </aside>

      <section className={hasSeries ? "split" : undefined}>
        {hasSeries ? <ForecastChart asOf={meta.asOf} series={bundle.series} supplier={meta.supplier} /> : null}
        <article className="card pad">
          <header>
            <h2>Категории (по наименованию)</h2>
            <p className="faint">Доля SKU к заказу. Отдельного справочника категорий в 1С нет.</p>
          </header>
          <ol className="bars">
            {categories.map((cat, i) => (
              <li key={cat.name}>
                <p>
                  <span>{i + 1}. {cat.name}</span>
                  <strong>{cat.toOrder} <span className="faint">({cat.share}%)</span></strong>
                </p>
                <div className="track"><span style={{ width: `${cat.share}%` }} /></div>
                <p className="faint">{cat.sku} SKU · пустой остаток: {cat.empty}</p>
              </li>
            ))}
          </ol>
        </article>
      </section>

      <section className="card">
        <header className="pad head">
          <div>
            <h2>Критичные позиции</h2>
            <p className="faint">Нажмите строку, чтобы открыть артикул. Полный список — в заказах.</p>
          </div>
          <Link href="/orders" className="btn">Все заказы</Link>
        </header>
        <table>
          <thead>
            <tr>
              <th>Артикул / наименование</th>
              <th>Остаток</th>
              <th>В пути</th>
              <th>Рек. заказ</th>
              <th>Статус</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((row) => (
              <tr key={row.code}>
                <td>
                  <Link href={`/sku/${encodeURIComponent(row.article)}`} className="thing">{cleanText(row.name)}</Link>
                  <p className="sku">{supplierArticle(row) ? `${supplierArticle(row)} · ` : ""}код 1С {row.code}</p>
                </td>
                <td>{row.stock} {row.unit}</td>
                <td>{row.inTransit}</td>
                <td>{row.recommended} {row.unit}</td>
                <td><StatusBadge tone={row.urgency} pulse /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
