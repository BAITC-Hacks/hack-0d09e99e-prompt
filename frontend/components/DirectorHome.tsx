"use client";

import { useEffect, useState } from "react";
import { formatQty, metaFrom } from "@/data/catalog";
import { Logo } from "./Logo";
import { useSession } from "./SessionProvider";
import { useWorkspace } from "./WorkspaceProvider";

type OrderState = {
  status: "draft" | "pending_approval" | "approved" | "returned";
  sentBy?: string | null;
  sentAt?: string | null;
  decidedBy?: string | null;
  comment?: string | null;
};

const titles: Record<OrderState["status"], string> = {
  draft: "Новых заказов нет",
  pending_approval: "Заказ ждёт вашего решения",
  approved: "Заказ утверждён",
  returned: "Заказ возвращён менеджеру",
};

function when(iso?: string | null) {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleString("ru-KZ", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

export function DirectorHome() {
  const { user, logout } = useSession();
  const { bundle } = useWorkspace();
  const meta = bundle ? metaFrom(bundle) : null;
  const kpis = bundle?.kpis;
  const [order, setOrder] = useState<OrderState | null>(null);

  useEffect(() => {
    let cancel = false;
    async function load() {
      const res = await fetch("/api/orders/current");
      if (!res.ok || cancel) return;
      setOrder((await res.json()) as OrderState);
    }
    void load();
    const timer = setInterval(() => void load(), 12000);
    return () => {
      cancel = true;
      clearInterval(timer);
    };
  }, []);

  const status = order?.status ?? "draft";
  const arrived = status === "pending_approval";

  return (
    <div className="gate">
      <section className="card import" aria-live="polite">
        <Logo title="" />
        <p className="caps">{user?.name} · {user?.title}</p>
        <h1>Уведомления</h1>
        <p className="lede">
          Таблицу закупа и настройки модели смотрит менеджер. Вам приходит только готовый заказ — утвердить его нужно в приложении.
        </p>
        {kpis && meta ? (
          <ul className="facts">
            <li>
              <p className="caps">Выгрузка</p>
              <strong>{meta.asOfLabel}</strong>
            </li>
            <li>
              <p className="caps">Позиций в заказе</p>
              <strong>{kpis.toOrder}</strong>
            </li>
            <li>
              <p className="caps">Критично</p>
              <strong>{kpis.critical}</strong>
            </li>
            <li>
              <p className="caps">В пути</p>
              <strong>{formatQty(kpis.inboundQty)} ед.</strong>
            </li>
          </ul>
        ) : null}
        <article className={arrived ? "card note" : "card pad"}>
          {!order ? (
            <p className="muted">Проверяем, нет ли новых заказов…</p>
          ) : (
            <>
              <p>{titles[status]}</p>
              {arrived ? (
                <p className="muted">
                  {order?.sentBy || "Менеджер"} отправила заказ {meta?.supplier || ""}
                  {order?.sentAt ? ` · ${when(order.sentAt)}` : ""}.
                  {bundle ? ` ${bundle.kpis.toOrder} позиций, из них ${bundle.kpis.critical} критичных.` : ""}
                  {" "}Поставщику ничего не ушло.
                </p>
              ) : status === "returned" ? (
                <p className="muted">{order?.comment || "Ждём, пока менеджер поправит заказ и отправит снова."}</p>
              ) : status === "approved" ? (
                <p className="muted">Утвердил {order?.decidedBy || "руководитель"}. Менеджер может выгрузить заказ в 1С.</p>
              ) : (
                <p className="muted">
                  Менеджер собирает заказ по выгрузке {meta?.asOfLabel || "1С"}. Когда он нажмёт «Отправить на согласование», карточка появится здесь сама.
                </p>
              )}
            </>
          )}
        </article>
        <button type="button" className="btn" onClick={() => void logout()}>
          Выйти
        </button>
      </section>
    </div>
  );
}
