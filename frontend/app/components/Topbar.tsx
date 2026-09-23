"use client";

import { metaFrom, peakSeasonFrom } from "@/app/data/catalog";
import { Icon } from "./Icon";
import { useWorkspace } from "./WorkspaceProvider";

export function Topbar({ onOpenSettings }: { onOpenSettings: () => void }) {
  const { bundle } = useWorkspace();
  const meta = bundle ? metaFrom(bundle) : null;
  const peak = bundle ? peakSeasonFrom(bundle) : null;

  return (
    <header className="fixed right-0 top-0 z-40 flex h-16 items-center justify-between gap-6 border-b border-line bg-card px-6" style={{ left: "var(--sidebar-width)" }}>
      <p className="text-[13px] text-ink-secondary">
        {bundle ? `${meta?.warehouse} · ${meta?.supplier}` : "Загрузите выгрузку, чтобы увидеть расчёт"}
      </p>
      <div className="flex shrink-0 items-center gap-3">
        {bundle ? (
          <>
            <span className="hidden rounded-full border border-status-critical-border bg-status-critical-bg px-2 py-1 text-[11px] font-medium text-status-critical xl:inline-flex">
              Критично: {bundle.kpis.critical}
            </span>
            <span className="hidden rounded-full border border-ai-insight-border bg-ai-insight-bg px-2 py-1 text-[11px] font-medium text-ai-insight xl:inline-flex">
              Сезон: {peak?.month} {peak?.coef}
            </span>
          </>
        ) : null}
        <button type="button" onClick={onOpenSettings} className="rounded-lg p-1.5 text-ink-secondary hover:bg-surface-low" aria-label="Параметры">
          <Icon name="tune" className="text-xl" />
        </button>
      </div>
    </header>
  );
}
