"use client";

import { useState } from "react";
import { DirectorHome } from "./DirectorHome";
import { LoginScreen } from "./LoginScreen";
import { SettingsDrawer } from "./SettingsDrawer";
import { useSession } from "./SessionProvider";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

export function AppShell({ children }: { children: React.ReactNode }) {
  const { user, ready } = useSession();
  const [settingsOpen, setSettingsOpen] = useState(false);

  if (!ready) {
    return (
      <div className="gate">
        <p className="muted">Проверяем вход…</p>
      </div>
    );
  }
  if (!user) return <LoginScreen />;
  if (user.role === "director") return <DirectorHome />;

  return (
    <div>
      <a href="#content" className="skip">
        К содержимому
      </a>
      <Sidebar onOpenSettings={() => setSettingsOpen(true)} />
      <Topbar onOpenSettings={() => setSettingsOpen(true)} />
      <main id="content">{children}</main>
      <SettingsDrawer open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  );
}
