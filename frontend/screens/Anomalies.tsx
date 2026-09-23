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
          Порог по каждому артикулу — скользящая медиана за 6 месяцев плюс 6×MAD.
          Месяц выше порога в регулярный спрос не входит: вместо него берётся медиана,
          поэтому разовая отгрузка не раздувает рекомендацию. Накладная, создавшая
          всплеск, найдена в «Динамике продаж».
        </p>
      </header>
      {anomalies.length > 0 ? (
        <div className="scroll">
          <table>
            <thead>
              <tr>
                <th>Месяц</th>
                <th>№ накладной</th>
                <th>Артикул</th>
                <th>Наименование</th>
                <th>Продажи за месяц</th>
                <th>Учтено в спросе</th>
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
