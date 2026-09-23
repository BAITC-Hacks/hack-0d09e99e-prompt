"use client";

import { ImportPanel } from "@/components/ImportPanel";
import { useWorkspace } from "@/components/WorkspaceProvider";
import { formatQty } from "@/data/catalog";

export function Suppliers() {
  const { bundle } = useWorkspace();
  if (!bundle) return <ImportPanel />;

  return (
    <section className="stack">
      <header>
        <h1>Поставщики</h1>
        <p className="lede">Поставщики берутся из загруженной выгрузки. Каталог в продукт не вшит.</p>
      </header>
      <ul className="suppliers">
        {bundle.suppliers.map((s) => (
          <li key={s.name} className="card pad">
            <h2>{s.name}</h2>
            <p className="muted">{s.role}</p>
            <dl>
              <div>
                <dt>SKU в MOQ</dt>
                <dd>{s.sku}</dd>
              </div>
              <div>
                <dt>Срок</dt>
                <dd>{s.lead}</dd>
              </div>
              <div>
                <dt>В пути, SKU</dt>
                <dd>{s.inbound}</dd>
              </div>
              <div>
                <dt>В пути, ед.</dt>
                <dd>{formatQty(s.inboundQty)}</dd>
              </div>
              <div>
                <dt>К заказу</dt>
                <dd>{s.toOrder}</dd>
              </div>
            </dl>
          </li>
        ))}
      </ul>
    </section>
  );
}
