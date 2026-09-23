"use client";

import { ImportPanel } from "../components/ImportPanel";
import { useWorkspace } from "../components/WorkspaceProvider";
import { formatQty } from "../data/catalog";

export default function AnomaliesPage() {
  const { bundle } = useWorkspace();
  if (!bundle) return <ImportPanel />;
  const { anomalies } = bundle;

  return (
    <section className="card overflow-hidden">
      <header className="border-b border-line p-4">
        <h1 className="text-2xl font-semibold tracking-tight text-ink">Разовые крупные заказы</h1>
        <p className="mt-1 text-[13px] text-ink-secondary">
          Расходные накладные из «Динамика продаж»: количество ≥ 1000 и ≥ 8 медиан SKU.
          Месяц с таким всплеском отсекается IQR при оценке спроса, поэтому в рекомендацию
          он не попадает. Построчного вычитания документа пока нет — спрос считается
          по помесячной выгрузке.
        </p>
      </header>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left text-[13px]">
          <thead>
            <tr className="bg-surface-low text-[11px] font-semibold uppercase tracking-wider text-ink-secondary">
              <th className="px-4 py-2.5">Дата</th>
              <th className="px-4 py-2.5">№ накладной</th>
              <th className="px-4 py-2.5">Артикул</th>
              <th className="px-4 py-2.5">Наименование</th>
              <th className="px-4 py-2.5 text-right">Кол-во</th>
              <th className="px-4 py-2.5 text-right">Медиана</th>
              <th className="px-4 py-2.5">Почему</th>
            </tr>
          </thead>
          <tbody>
            {anomalies.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-ink-secondary">
                  В этой выгрузке разовых всплесков нет.
                </td>
              </tr>
            ) : (
              anomalies.map((row) => (
                <tr key={`${row.invoice}-${row.code}`} className="border-t border-line hover:bg-surface-low/70">
                  <td className="px-4 py-3">{row.date}</td>
                  <td className="px-4 py-3 font-medium">{row.invoice}</td>
                  <td className="mono-sku px-4 py-3 text-primary-container">{row.article}</td>
                  <td className="px-4 py-3">{row.name}</td>
                  <td className="px-4 py-3 text-right tabular-nums font-semibold text-status-warning">{formatQty(row.qty)}</td>
                  <td className="px-4 py-3 text-right tabular-nums">{formatQty(row.median)}</td>
                  <td className="px-4 py-3 text-ink-secondary">{row.reason}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
