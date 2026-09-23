"use client";

import { metaFrom, modelFrom, peakSeasonFrom } from "@/data/catalog";
import { Icon } from "./Icon";
import { useWorkspace } from "./WorkspaceProvider";

export function Topbar({ onOpenSettings }: { onOpenSettings: () => void }) {
  const { bundle } = useWorkspace();
  const meta = bundle ? metaFrom(bundle) : null;
  const peak = bundle ? peakSeasonFrom(bundle) : null;
  const model = bundle ? modelFrom(bundle) : null;

  return (
    <header className="bar">
      <p>{bundle ? `Закупки · ${meta?.supplier}` : "Загрузите выгрузку, чтобы увидеть расчёт"}</p>
      <div className="bar-tools">
        {bundle ? <span className="chip-critical">Критично: {bundle.kpis.critical}</span> : null}
        {model ? <span className="chip-insight">{model.label}</span> : null}
        {peak ? <span className="chip-insight">Сезон: {peak.month} {peak.coef}</span> : null}
        <button type="button" onClick={onOpenSettings} className="icon-btn" aria-label="Как считает модель">
          <Icon name="tune" />
        </button>
      </div>
    </header>
  );
}
