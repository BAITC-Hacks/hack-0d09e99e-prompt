"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useWorkspace } from "./WorkspaceProvider";
import { Logo } from "./Logo";

const slots = [
  "Ежемесячные продажи",
  "Ежемесячные остатки",
  "Динамика продаж",
  "Товары в пути",
  "MOQ",
  "Сезонность",
];

export function ImportPanel() {
  const router = useRouter();
  const { setBundle } = useWorkspace();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function send(body: FormData | null, demo = false) {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`/api/import${demo ? "?demo=1" : ""}`, {
        method: "POST",
        body: demo ? undefined : body ?? undefined,
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || "не удалось посчитать");
      setBundle(json.bundle);
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "ошибка");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card import">
      <Logo title="" />
      <h1>Загрузите выгрузку 1С</h1>
      <p className="lede">
        Qor не хранит чужой каталог внутри продукта. Менеджер выгружает Excel из 1С — отсюда считаются заказы.
        Модель дообучается отдельно; этот шаг только принимает файлы и запускает расчёт.
      </p>
      <ul className="slots">
        {slots.map((s) => (
          <li key={s}>{s}</li>
        ))}
      </ul>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          void send(new FormData(e.currentTarget));
        }}
      >
        <label>
          <span className="skip">Файлы xlsx</span>
          <input name="files" type="file" accept=".xlsx,.xls" multiple required />
        </label>
        <div className="actions">
          <button type="submit" disabled={busy} className="btn btn-primary">
            {busy ? "Считаем…" : "Посчитать заказы"}
          </button>
          <button type="button" disabled={busy} className="btn" onClick={() => void send(null, true)}>
            Демо: выгрузка IEK с диска
          </button>
        </div>
      </form>
      {error ? <p className="error">{error}</p> : null}
    </section>
  );
}
