"use client";

import { ImportPanel } from "../components/ImportPanel";
import { useWorkspace } from "../components/WorkspaceProvider";
import { formatQty } from "../data/catalog";

export default function SuppliersPage() {
  const { bundle } = useWorkspace();
  if (!bundle) return <ImportPanel />;

  return (
    <section>
      <header className="mb-4">
        <h1 className="text-2xl font-semibold tracking-tight text-ink">Поставщики</h1>
        <p className="text-[13px] text-ink-secondary">
          Поставщики берутся из загруженной выгрузки. Каталог в продукт не вшит.
        </p>
      </header>
      <ul className="grid gap-3 md:grid-cols-2">
        {bundle.suppliers.map((s) => (
          <li key={s.name} className="card p-4">
            <h2 className="text-lg font-semibold text-ink">{s.name}</h2>
            <p className="text-xs text-ink-secondary">{s.role}</p>
            <dl className="mt-3 grid grid-cols-2 gap-2 text-[13px]">
              <div>
                <dt className="text-ink-muted">SKU в MOQ</dt>
                <dd className="font-medium">{s.sku}</dd>
              </div>
              <div>
                <dt className="text-ink-muted">Срок</dt>
                <dd className="font-medium">{s.lead}</dd>
              </div>
              <div>
                <dt className="text-ink-muted">В пути, SKU</dt>
                <dd className="font-medium">{s.inbound}</dd>
              </div>
              <div>
                <dt className="text-ink-muted">В пути, ед.</dt>
                <dd className="font-medium">{formatQty(s.inboundQty)}</dd>
              </div>
              <div>
                <dt className="text-ink-muted">К заказу</dt>
                <dd className="font-medium">{s.toOrder}</dd>
              </div>
            </dl>
          </li>
        ))}
      </ul>
    </section>
  );
}
