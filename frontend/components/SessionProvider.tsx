"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";

export type SessionUser = {
  username: string;
  role: "buyer" | "director";
  name: string;
  title: string;
};

type Ctx = {
  user: SessionUser | null;
  ready: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

const SessionContext = createContext<Ctx>({
  user: null,
  ready: false,
  login: async () => undefined,
  logout: async () => undefined,
});

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<SessionUser | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancel = false;
    fetch("/api/auth/me")
      .then(async (res) => {
        if (!res.ok) return null;
        return (await res.json()) as SessionUser;
      })
      .then((next) => {
        if (!cancel) setUser(next);
      })
      .finally(() => {
        if (!cancel) setReady(true);
      });
    return () => {
      cancel = true;
    };
  }, []);

  const value = useMemo<Ctx>(
    () => ({
      user,
      ready,
      async login(username, password) {
        const res = await fetch("/api/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Не удалось войти");
        setUser(data);
      },
      async logout() {
        await fetch("/api/auth/logout", { method: "POST" });
        setUser(null);
      },
    }),
    [user, ready],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession() {
  return useContext(SessionContext);
}
