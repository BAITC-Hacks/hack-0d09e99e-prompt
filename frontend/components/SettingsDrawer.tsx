"use client";

import { modelFrom } from "@/data/catalog";
import { Icon } from "./Icon";
import { useWorkspace } from "./WorkspaceProvider";

export function SettingsDrawer({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { bundle } = useWorkspace();
  if (!open) return null;
  const model = bundle ? modelFrom(bundle) : null;

  return (
    <div className="drawer" role="dialog" aria-modal="true" aria-labelledby="settings-title">
      <button type="button" aria-label="Закрыть" onClick={onClose} />
      <aside>
        <header>
          <div>
            <p className="caps">Модель спроса</p>
            <h2 id="settings-title">Как считает Qor</h2>
          </div>
          <button type="button" onClick={onClose} className="icon-btn" aria-label="Закрыть">
            <Icon name="close" />
          </button>
        </header>

        <div className="body">
          {model ? (
            <>
              <section className="stack">
                <h3>1. Что считает модель</h3>
                <p className="lede">
                  {model.label} предсказывает {model.target} в штуках. Это не среднее за прошлый год и не ползунок горизонта.
                </p>
                <ul className="recipe">
                  {model.uses.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
                <p className="faint">{model.name}</p>
              </section>

              <section className="stack">
                <h3>2. Как из прогноза получается заказ</h3>
                <ol className="waterfall">
                  <li>
                    <span>
                      <span className="num">1</span>
                      Прогноз модели
                    </span>
                    <strong>база</strong>
                  </li>
                  <li>
                    <span>
                      <span className="num">2</span>
                      Страховой запас
                    </span>
                    <strong>+ 0.5σ</strong>
                  </li>
                  <li>
                    <span>
                      <span className="num">3</span>
                      Остаток на складе
                    </span>
                    <strong>−</strong>
                  </li>
                  <li>
                    <span>
                      <span className="num">4</span>
                      Уже в пути
                    </span>
                    <strong>−</strong>
                  </li>
                  <li>
                    <span>
                      <span className="num">5</span>
                      Округление до MOQ
                    </span>
                    <strong>рек.</strong>
                  </li>
                </ol>
                <p className="muted">{model.policy}</p>
              </section>

              <section className="stack">
                <h3>3. Что здесь нельзя крутить</h3>
                <p className="muted">
                  Горизонт задаёт сама модель — месяц вперёд. Ползунки сезонности и аномалий заказ не пересчитывают: это уже внутри признаков.
                  Количество правится в таблице, решение — у руководителя в приложении.
                </p>
              </section>
            </>
          ) : (
            <p className="muted">Сначала загрузите выгрузку 1С — тогда здесь появится живая модель.</p>
          )}
        </div>

        <footer>
          <button type="button" onClick={onClose} className="btn btn-primary">
            Понятно
          </button>
        </footer>
      </aside>
    </div>
  );
}
