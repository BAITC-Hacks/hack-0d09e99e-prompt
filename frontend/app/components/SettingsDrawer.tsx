"use client";

import { metaFrom, peakSeasonFrom } from "@/app/data/catalog";
import { Icon } from "./Icon";
import { useWorkspace } from "./WorkspaceProvider";

export function SettingsDrawer({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { bundle } = useWorkspace();
  if (!open) return null;
  const meta = bundle
    ? metaFrom(bundle)
    : { horizonWeeks: 8, supplier: "—", monthEquiv: 2 };
  const peakSeason = bundle ? peakSeasonFrom(bundle) : { month: "—", coef: 1 };

  return (
    <div className="fixed inset-0 z-[60]" role="dialog" aria-modal="true" aria-labelledby="settings-title">
      <button type="button" className="absolute inset-0 bg-ink/45 backdrop-blur-[4px]" aria-label="Закрыть" onClick={onClose} />
      <aside className="absolute right-0 top-0 flex h-full w-full max-w-md flex-col bg-card shadow-drawer">
        <header className="flex items-center justify-between border-b border-line px-5 py-4">
          <div>
            <p className="label-caps">Модель спроса</p>
            <h2 id="settings-title" className="text-lg font-semibold text-ink">
              Параметры Qor
            </h2>
          </div>
          <button type="button" onClick={onClose} className="rounded-lg p-1 text-ink-secondary hover:bg-surface-low" aria-label="Закрыть">
            <Icon name="close" className="text-xl" />
          </button>
        </header>

        <div className="flex-1 space-y-6 overflow-y-auto px-5 py-5">
          <section>
            <h3 className="mb-3 text-[13px] font-semibold text-ink">1. Горизонт планирования</h3>
            <div className="grid grid-cols-4 gap-2">
              {[4, 8, 12, 26].map((weeks) => {
                const active = weeks === meta.horizonWeeks;
                return (
                  <button
                    key={weeks}
                    type="button"
                    aria-pressed={active}
                    className={`rounded-lg border px-2 py-2 text-xs font-medium ${
                      active ? "border-primary-container bg-primary-fixed text-primary" : "border-line text-ink-secondary"
                    }`}
                  >
                    {weeks} нед
                    {active ? <span className="mt-0.5 block text-[10px] text-primary-container">Текущий</span> : null}
                  </button>
                );
              })}
            </div>
          </section>

          <section className="space-y-3">
            <h3 className="text-[13px] font-semibold text-ink">2. Сезонность и рост</h3>
            {[
              {
                title: `Учитывать сезонность ${meta.supplier}`,
                hint: `Горизонт ×${meta.monthEquiv}, пик ${peakSeason.month} ${peakSeason.coef}`,
                on: true,
              },
              {
                title: "Компенсация stockout",
                hint: "Месяцы без остатка исключены из оценки спроса",
                on: true,
              },
              {
                title: "Устойчивый тренд роста",
                hint: "Не реализовано — спрос берётся по медиане без наклона",
                on: false,
              },
            ].map(({ title, hint, on }) => (
              <label
                key={title}
                className={`flex items-start justify-between gap-3 rounded-xl border border-line p-3 ${on ? "" : "opacity-60"}`}
              >
                <span>
                  <strong className="block text-[13px] font-medium text-ink">{title}</strong>
                  <span className="text-xs text-ink-secondary">{hint}</span>
                </span>
                <input
                  type="checkbox"
                  defaultChecked={on}
                  disabled={!on}
                  className="mt-1 accent-primary-container"
                />
              </label>
            ))}
          </section>

          <section>
            <h3 className="mb-2 text-[13px] font-semibold text-ink">3. Чувствительность к аномалиям</h3>
            <input type="range" min={1} max={3} defaultValue={2} className="w-full accent-primary-container" />
            <p className="mt-1 text-xs text-ink-secondary">IQR / p99 по расходным накладным. Клиентов в данных нет — ловим по номеру документа.</p>
          </section>
        </div>

        <footer className="flex gap-2 border-t border-line p-4">
          <button type="button" onClick={onClose} className="flex-1 rounded-lg bg-primary py-2.5 text-[13px] font-medium text-white">
            Применить и пересчитать
          </button>
          <button type="button" onClick={onClose} className="rounded-lg border border-line px-4 text-[13px] font-medium text-ink">
            Отмена
          </button>
        </footer>
      </aside>
    </div>
  );
}
