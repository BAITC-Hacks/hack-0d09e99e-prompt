"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { featuredArticle, kpis } from "@/app/data/catalog";
import { Icon } from "./Icon";

const nav = [
  { href: "/", label: "Дашборд", icon: "dashboard" },
  { href: "/orders", label: "Заказы поставщикам", icon: "assignment_turned_in", badge: kpis.toOrder },
  { href: `/sku/${encodeURIComponent(featuredArticle)}`, label: "Аналитика SKU", icon: "analytics" },
  { href: "/anomalies", label: "Аномалии", icon: "report" },
  { href: "/suppliers", label: "Поставщики", icon: "local_shipping" },
];

export function Sidebar({ onOpenSettings }: { onOpenSettings: () => void }) {
  const pathname = usePathname();

  return (
    <aside className="fixed inset-y-0 left-0 z-50 flex w-64 flex-col justify-between border-r border-line bg-card">
      <div>
        <div className="flex flex-col gap-2 border-b border-line p-4">
          <Link href="/" className="flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-sm font-bold text-white">
              Q
            </span>
            <span>
              <strong className="block text-base font-semibold leading-tight text-ink">Qor</strong>
              <span className="label-caps">ekt.kz · запас</span>
            </span>
          </Link>
          <p className="flex items-center gap-1 rounded-lg border border-line bg-surface-low px-2 py-1 text-xs text-ink">
            <Icon name="warehouse" className="text-base text-primary-container" />
            Склад Алматы · IEK
          </p>
        </div>

        <p className="label-caps px-5 pb-2 pt-3">Навигация</p>
        <nav aria-label="Основная навигация" className="flex flex-col gap-1 px-2">
          {nav.map((item) => {
            const active =
              item.href === "/"
                ? pathname === "/"
                : item.href.startsWith("/sku/")
                  ? pathname.startsWith("/sku/")
                  : pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={`flex items-center justify-between rounded-lg px-2 py-2 text-[13px] font-medium transition-colors ${
                  active
                    ? "bg-primary text-white shadow-sm"
                    : "text-ink-secondary hover:bg-surface-low hover:text-ink"
                }`}
              >
                <span className="flex items-center gap-3">
                  <Icon name={item.icon} className="text-lg" />
                  {item.label}
                </span>
                {item.badge ? (
                  <span className="rounded-full border border-status-critical-border bg-status-critical-bg px-1.5 text-[11px] font-semibold text-status-critical">
                    {item.badge}
                  </span>
                ) : null}
              </Link>
            );
          })}
          <button
            type="button"
            onClick={onOpenSettings}
            className="flex items-center gap-3 rounded-lg px-2 py-2 text-left text-[13px] font-medium text-ink-secondary hover:bg-surface-low hover:text-ink"
          >
            <Icon name="settings" className="text-lg" />
            Настройки
          </button>
        </nav>
      </div>

      <footer className="border-t border-line">
        <div className="flex items-center justify-between border-b border-line px-4 py-2">
          <p className="text-xs text-ink-secondary">Выгрузка 1С · 22.09.2026</p>
          <button type="button" onClick={onOpenSettings} className="text-[11px] font-semibold text-primary-container">
            Параметры
          </button>
        </div>
        <div className="p-4">
          <p className="text-[13px] font-medium text-ink">Менеджер закупа</p>
          <p className="text-[11px] text-ink-secondary">Роль · только просмотр расчёта</p>
        </div>
      </footer>
    </aside>
  );
}
