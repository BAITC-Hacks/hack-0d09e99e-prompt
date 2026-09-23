"use client";

import { ImportPanel } from "@/components/ImportPanel";
import { useWorkspace } from "@/components/WorkspaceProvider";
import { formatQty } from "@/data/catalog";

export function Anomalies() {
  const { bundle } = useWorkspace();
  if (!bundle) return <ImportPanel />;
  const { anomalies } = bundle;

  return (
    <section className="card">
      <header className="pad">
        <h1>Разовые крупные заказы</h1>
        <p className="lede">
          Расходные накладные из «Динамика продаж»: количество ≥ 1000 и ≥ 8 медиан SKU.
          Месяц с таким всплеском отсекается IQR при оценке спроса, поэтому в рекомендацию
          он не попадает. Построчного вычитания документа пока нет — спрос считается
          по помесячной выгрузке.
        </p>
      </header>
      {anomalies.length > 0 ? (
        <div className="scroll">
          <table>
            <thead>
              <tr>
                <th>Дата</th>
                <th>№ накладной</th>
                <th>Артикул</th>
                <th>Наименование</th>
                <th>Кол-во</th>
                <th>Медиана</th>
                <th>Почему</th>
              </tr>
            </thead>
            <tbody>
              {anomalies.map((row) => (
                <tr key={`${row.invoice}-${row.code}`}>
                  <td>{row.date}</td>
                  <td>{row.invoice}</td>
                  <td className="article">{row.article}</td>
                  <td>{row.name}</td>
                  <td>{formatQty(row.qty)}</td>
                  <td>{formatQty(row.median)}</td>
                  <td className="muted">{row.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}
