"use client";

import { Icon } from "./Icon";

export function SettingsDrawer({ open, onClose }: { open: boolean; onClose: () => void }) {
  if (!open) return null;

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
              {["4 нед", "8 нед", "12 нед", "26 нед"].map((label, i) => (
                <button
                  key={label}
                  type="button"
                  className={`rounded-lg border px-2 py-2 text-xs font-medium ${
                    i === 1 ? "border-primary-container bg-primary-fixed text-primary" : "border-line text-ink-secondary"
                  }`}
                >
                  {label}
                  {i === 1 ? <span className="mt-0.5 block text-[10px] text-primary-container">Реком.</span> : null}
                </button>
              ))}
            </div>
          </section>

          <section className="space-y-3">
            <h3 className="text-[13px] font-semibold text-ink">2. Сезонность и рост</h3>
            {[
              ["Учитывать сезонность IEK", "Пик июль 1.22 / октябрь 1.24"],
              ["Устойчивый тренд роста", "Наклон 12 мес. после очистки выбросов"],
              ["Компенсация stockout", "Пустые остатки не считаем нулевым спросом"],
            ].map(([title, hint]) => (
              <label key={title} className="flex items-start justify-between gap-3 rounded-xl border border-line p-3">
                <span>
                  <strong className="block text-[13px] font-medium text-ink">{title}</strong>
                  <span className="text-xs text-ink-secondary">{hint}</span>
                </span>
                <input type="checkbox" defaultChecked className="mt-1 accent-primary-container" />
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
