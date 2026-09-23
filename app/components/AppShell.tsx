"use client";

import { useState } from "react";
import { SettingsDrawer } from "./SettingsDrawer";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [recalcAt, setRecalcAt] = useState("22.09.2026 16:04");

  return (
    <div>
      <a href="#content" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[70] focus:rounded-lg focus:bg-primary focus:px-3 focus:py-2 focus:text-white">
        К содержимому
      </a>
      <Sidebar onOpenSettings={() => setSettingsOpen(true)} />
      <Topbar
        onOpenSettings={() => setSettingsOpen(true)}
        onRecalc={() => setRecalcAt(new Date().toLocaleString("ru-RU"))}
      />
      <main id="content" className="shell-main px-6 pb-8">
        <p className="sr-only">Последний пересчёт: {recalcAt}</p>
        {children}
      </main>
      <SettingsDrawer open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  );
}
