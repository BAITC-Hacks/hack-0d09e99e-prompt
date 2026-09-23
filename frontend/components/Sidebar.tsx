"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { metaFrom } from "@/data/catalog";
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
    <aside className="nav">
      <div>
        <div className="nav-brand">
          <Link href="/" className="brand">
            <Logo title="" />
            <span>Qor</span>
          </Link>
          {meta ? (
            <p className="warehouse">
              <Icon name="warehouse" />
              Склад {meta.warehouse} · {meta.supplier}
            </p>
          ) : (
            <p className="quiet">Нет выгрузки — загрузите Excel из 1С</p>
          )}
        </div>

        <p className="caps">Навигация</p>
        <nav aria-label="Основная навигация">
          {nav.map((item) => {
            const active =
              item.href === "/"
                ? pathname === "/"
                : item.href.startsWith("/sku/")
                  ? pathname.startsWith("/sku/")
                  : pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link key={item.label} href={item.href} aria-current={active ? "page" : undefined}>
                <span>
                  <Icon name={item.icon} />
                  {item.label}
                </span>
                {item.badge ? <span className="count">{item.badge}</span> : null}
              </Link>
            );
          })}
          <button type="button" onClick={onOpenSettings}>
            <Icon name="settings" />
            Настройки
          </button>
        </nav>
      </div>

      <footer>
        <p>{bundle ? `Выгрузка · ${meta?.asOfLabel}` : "Ожидает файл 1С"}</p>
      </footer>
    </aside>
  );
}
