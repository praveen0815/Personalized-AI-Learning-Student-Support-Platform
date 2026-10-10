"use client";

import { createContext, useContext, useMemo, useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";

type ShellContextValue = {
  setTitle: (title: string) => void;
};

const ShellContext = createContext<ShellContextValue | null>(null);

export function useShell() {
  const value = useContext(ShellContext);
  if (!value) {
    throw new Error("useShell must be used inside AppShell");
  }
  return value;
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const [title, setTitle] = useState("Dashboard");
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const shell = useMemo(() => ({ setTitle }), []);

  return (
    <ShellContext.Provider value={shell}>
      <div className="min-h-screen bg-slate-50 text-slate-900">
        <div className="md:flex">
          <Sidebar
            collapsed={collapsed}
            mobileOpen={mobileOpen}
            onNavigate={() => setMobileOpen(false)}
            onToggleCollapsed={() => setCollapsed((value) => !value)}
          />
          <div className="min-w-0 flex-1">
            <Topbar title={title} onOpenMenu={() => setMobileOpen(true)} />
            <main className="px-4 py-4 md:px-6 md:py-6">{children}</main>
          </div>
        </div>
      </div>
    </ShellContext.Provider>
  );
}
