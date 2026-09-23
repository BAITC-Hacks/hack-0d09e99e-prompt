"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { metaFrom } from "@/app/data/catalog";
import { Icon } from "./Icon";
import { Logo } from "./Logo";
import { useWorkspace } from "./WorkspaceProvider";

export function Sidebar({ onOpenSettings }: { onOpenSettings: () => void }) {
  const pathname = usePathname();
  const { bundle } = useWorkspace();
  const meta = bundle ? metaFrom(bundle) : null;
  const featured = bundle?.featuredArticle;
  const toOrder = bundle?.kpis.toOrder;

  const nav = [
    { href: "/", label: "Дашборд", icon: "dashboard" },
    { href: "/import", label: "Выгрузка 1С", icon: "upload_file" },
    { href: "/orders", label: "Заказы поставщикам", icon: "assignment_turned_in", badge: toOrder },
    { href: featured ? `/sku/${encodeURIComponent(featured)}` : "/import", label: "Аналитика SKU", icon: "analytics" },
    { href: "/anomalies", label: "Аномалии", icon: "report" },
    { href: "/suppliers", label: "Поставщики", icon: "local_shipping" },
  ];

  return (
    <aside className="fixed inset-y-0 left-0 z-50 flex w-64 flex-col justify-between border-r border-line bg-card">
      <div>
        <div className="flex flex-col gap-2 border-b border-line p-4">
          <Link href="/" className="flex items-center gap-2.5 text-primary">
            <Logo className="h-9 w-9" title="" />
            <span className="text-[22px] font-semibold leading-none tracking-tight text-ink">Qor</span>
          </Link>
          {meta ? (
            <p className="flex items-center gap-1 rounded-lg border border-line bg-surface-low px-2 py-1 text-xs text-ink">
              <Icon name="warehouse" className="text-base text-primary-container" />
              Склад {meta.warehouse} · {meta.supplier}
            </p>
          ) : (
            <p className="text-xs text-ink-muted">Нет выгрузки — загрузите Excel из 1С</p>
          )}
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
                key={item.label}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={`flex items-center justify-between rounded-lg px-2 py-2 text-[13px] font-medium transition-colors ${
                  active ? "bg-primary text-white shadow-sm" : "text-ink-secondary hover:bg-surface-low hover:text-ink"
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

      <footer className="border-t border-line px-4 py-3">
        <p className="text-xs text-ink-secondary">{bundle ? `Выгрузка · ${meta?.asOfLabel}` : "Ожидает файл 1С"}</p>
      </footer>
    </aside>
  );
}
