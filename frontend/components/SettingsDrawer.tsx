"use client";

import { metaFrom, peakSeasonFrom } from "@/data/catalog";
import { Icon } from "./Icon";
import { useWorkspace } from "./WorkspaceProvider";

export function SettingsDrawer({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { bundle } = useWorkspace();
  if (!open) return null;
  const meta = bundle ? metaFrom(bundle) : null;
  const peakSeason = bundle ? peakSeasonFrom(bundle) : null;

  return (
    <div className="drawer" role="dialog" aria-modal="true" aria-labelledby="settings-title">
      <button type="button" aria-label="Закрыть" onClick={onClose} />
      <aside>
        <header>
          <div>
            <p className="caps">Модель спроса</p>
            <h2 id="settings-title">Параметры Qor</h2>
          </div>
          <button type="button" onClick={onClose} className="icon-btn" aria-label="Закрыть">
            <Icon name="close" />
          </button>
        </header>

        <div className="body">
          <section className="stack">
            <h3>1. Горизонт планирования</h3>
            <div className="weeks">
              {[4, 8, 12, 26].map((weeks) => {
                const active = weeks === meta?.horizonWeeks;
                return (
                  <button key={weeks} type="button" aria-pressed={active}>
                    {weeks} нед
                    {active ? <span>Текущий</span> : null}
                  </button>
                );
              })}
            </div>
          </section>

          <section className="stack">
            <h3>2. Сезонность и рост</h3>
            {[
              ...(peakSeason && meta
                ? [{
                    title: `Учитывать сезонность ${meta.supplier}`,
                    hint: `Горизонт ×${meta.monthEquiv}, пик ${peakSeason.month} ${peakSeason.coef}`,
                    on: true,
                  }]
                : []),
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
              <label key={title} className="option" data-off={on ? undefined : "true"}>
                <span>
                  <strong>{title}</strong>
                  <span>{hint}</span>
                </span>
                <input type="checkbox" defaultChecked={on} disabled={!on} />
              </label>
            ))}
          </section>

          <section className="stack">
            <h3>3. Чувствительность к аномалиям</h3>
            <input type="range" min={1} max={3} defaultValue={2} />
            <p className="muted">IQR / p99 по расходным накладным. Клиентов в данных нет — ловим по номеру документа.</p>
          </section>
        </div>

        <footer>
          <button type="button" onClick={onClose} className="btn btn-primary">
            Применить и пересчитать
          </button>
          <button type="button" onClick={onClose} className="btn">
            Отмена
          </button>
        </footer>
      </aside>
    </div>
  );
}
