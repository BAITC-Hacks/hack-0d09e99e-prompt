"use client";

import { createContext, useContext, useMemo, useState } from "react";
import type { WorkspaceBundle } from "@/app/data/catalog";

type Ctx = {
  bundle: WorkspaceBundle | null;
  setBundle: (b: WorkspaceBundle | null) => void;
};

const WorkspaceContext = createContext<Ctx>({ bundle: null, setBundle: () => undefined });

export function WorkspaceProvider({
  initial,
  children,
}: {
  initial: WorkspaceBundle | null;
  children: React.ReactNode;
}) {
  const [bundle, setBundle] = useState(initial);
  const value = useMemo(() => ({ bundle, setBundle }), [bundle]);
  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}

export function useWorkspace() {
  return useContext(WorkspaceContext);
}
