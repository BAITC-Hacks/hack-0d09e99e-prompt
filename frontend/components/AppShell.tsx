"use client";

import { useState } from "react";
import { SettingsDrawer } from "./SettingsDrawer";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [settingsOpen, setSettingsOpen] = useState(false);

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
