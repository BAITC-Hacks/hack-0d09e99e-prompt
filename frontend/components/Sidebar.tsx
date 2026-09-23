"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { metaFrom } from "@/data/catalog";
import { Icon } from "./Icon";
import { Logo } from "./Logo";
import { useSession } from "./SessionProvider";
import { useWorkspace } from "./WorkspaceProvider";

export function Sidebar({ onOpenSettings }: { onOpenSettings: () => void }) {
  const pathname = usePathname();
  const { bundle } = useWorkspace();
  const { user, logout } = useSession();
  const meta = bundle ? metaFrom(bundle) : null;
  const toOrder = bundle?.kpis.toOrder;

  const nav = [
    { href: "/", label: "Дашборд", icon: "dashboard" },
    { href: "/import", label: "Выгрузка 1С", icon: "upload_file" },
    { href: "/orders", label: "Заказы поставщикам", icon: "assignment_turned_in", badge: toOrder },
    { href: "/anomalies", label: "Аномалии", icon: "report" },
    { href: "/suppliers", label: "Поставщики", icon: "local_shipping" },
  ];

  return (
    <aside className="nav">
      <div>
        <div className="nav-brand">
          <Link href="/" className="brand">
            <span className="brand-mark">
              <Logo title="" />
            </span>
            <span className="brand-copy">
              <span className="brand-name">Qor</span>
              <span className="brand-tag">Закупки ekt.kz</span>
            </span>
          </Link>
          {meta ? (
            <p className="warehouse">
              <Icon name="local_shipping" />
              {meta.supplier}
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
            Как считает
          </button>
        </nav>
      </div>

      <footer>
        {user ? (
          <p>
            {user.name} · {user.title}
          </p>
        ) : null}
        <p>{bundle ? `Выгрузка · ${meta?.asOfLabel}` : "Ожидает файл 1С"}</p>
        <button type="button" className="btn" onClick={() => void logout()}>
          Выйти
        </button>
      </footer>
    </aside>
  );
}
