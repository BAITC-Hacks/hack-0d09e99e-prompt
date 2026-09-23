import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { AppShell } from "@/components/AppShell";
import { WorkspaceProvider } from "@/components/WorkspaceProvider";
import { readWorkspace } from "@/data/workspace";
import "./globals.css";

const inter = Inter({
  subsets: ["latin", "cyrillic"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Qor — закупки ekt.kz",
  description: "Qor: загрузите выгрузку 1С — получите заказы поставщикам.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const initial = readWorkspace();
  return (
    <html lang="ru" className={inter.variable}>
      <head>
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,400..600,0..1,0&display=swap"
        />
      </head>
      <body>
        <WorkspaceProvider initial={initial}>
          <AppShell>{children}</AppShell>
        </WorkspaceProvider>
      </body>
    </html>
  );
}
