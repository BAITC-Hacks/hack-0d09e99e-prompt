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
    <section className="card mx-auto max-w-2xl p-8">
      <Logo className="mb-4 h-12 w-12 text-primary" />
      <h1 className="text-2xl font-semibold tracking-tight text-ink">Загрузите выгрузку 1С</h1>
      <p className="mt-2 text-[13px] text-ink-secondary">
        Qor не хранит чужой каталог внутри продукта. Менеджер выгружает Excel из 1С — отсюда считаются заказы.
        Модель дообучается отдельно; этот шаг только принимает файлы и запускает расчёт.
      </p>
      <ul className="mt-4 grid grid-cols-2 gap-2 text-xs text-ink-secondary">
        {slots.map((s) => (
          <li key={s} className="rounded-lg border border-line bg-surface-low/50 px-3 py-2">
            {s}
          </li>
        ))}
      </ul>
      <form
        className="mt-6 flex flex-col gap-3"
        onSubmit={(e) => {
          e.preventDefault();
          const form = new FormData(e.currentTarget);
          void send(form);
        }}
      >
        <label className="block">
          <span className="sr-only">Файлы xlsx</span>
          <input name="files" type="file" accept=".xlsx,.xls" multiple required className="w-full text-[13px]" />
        </label>
        <div className="flex flex-wrap gap-2">
          <button type="submit" disabled={busy} className="rounded-lg bg-primary px-4 py-2 text-[13px] font-medium text-white disabled:opacity-50">
            {busy ? "Считаем…" : "Посчитать заказы"}
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => void send(null, true)}
            className="rounded-lg border border-line px-4 py-2 text-[13px] font-medium text-ink"
          >
            Демо: выгрузка IEK с диска
          </button>
        </div>
      </form>
      {error ? <p className="mt-3 text-sm text-status-critical">{error}</p> : null}
    </section>
  );
}
