"use client";

import { kpis } from "@/app/data/catalog";
import { Icon } from "./Icon";

export function Topbar({ onRecalc, onOpenSettings }: { onRecalc?: () => void; onOpenSettings: () => void }) {
  return (
    <header className="fixed right-0 top-0 z-40 flex h-16 items-center justify-between gap-6 border-b border-line bg-card px-6" style={{ left: "var(--sidebar-width)" }}>
      <form role="search" className="relative max-w-xl flex-1" onSubmit={(e) => e.preventDefault()}>
        <Icon name="search" className="absolute left-3 top-1/2 -translate-y-1/2 text-lg text-ink-muted" />
        <input
          type="search"
          name="q"
          placeholder="Поиск по артикулу IEK или коду 1С"
          className="w-full rounded-lg border border-line bg-surface-low py-1.5 pl-9 pr-3 text-[13px] text-ink placeholder:text-ink-muted focus:border-line-focus focus:outline-none focus:ring-1 focus:ring-line-focus"
        />
      </form>

      <div className="flex shrink-0 items-center gap-4">
        <div className="hidden items-center gap-2 xl:flex">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-status-critical-border bg-status-critical-bg px-2 py-1 text-[11px] font-medium text-status-critical">
            <span className="h-1.5 w-1.5 rounded-full bg-status-critical" />
            Критично: {kpis.critical}
          </span>
          <span className="inline-flex items-center gap-1.5 rounded-full border border-ai-insight-border bg-ai-insight-bg px-2 py-1 text-[11px] font-medium text-ai-insight">
            <Icon name="auto_awesome" className="text-sm" />
            Сезонность IEK: окт 1.24
          </span>
        </div>
        <span className="hidden h-5 w-px bg-line xl:block" />
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onRecalc}
            className="inline-flex items-center gap-1 rounded-lg bg-primary px-3 py-1.5 text-[13px] font-medium text-white shadow-sm hover:bg-primary-container"
          >
            <Icon name="refresh" className="text-lg" />
            Пересчитать
          </button>
          <button type="button" onClick={onOpenSettings} className="rounded-lg p-1.5 text-ink-secondary hover:bg-surface-low" aria-label="Параметры расчёта">
            <Icon name="tune" className="text-xl" />
          </button>
        </div>
      </div>
    </header>
  );
}
