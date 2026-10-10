"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { brand } from "@/lib/brand";
import { cn } from "@/lib/format";
import { navigation } from "@/lib/navigation";

export function Sidebar({
  collapsed,
  mobileOpen,
  onNavigate,
  onToggleCollapsed,
}: {
  collapsed: boolean;
  mobileOpen: boolean;
  onNavigate: () => void;
  onToggleCollapsed: () => void;
}) {
  const pathname = usePathname();

  return (
    <>
      {mobileOpen ? (
        <button
          type="button"
          className="fixed inset-0 z-30 bg-slate-900/40 md:hidden"
          aria-label="Close navigation"
          onClick={onNavigate}
        />
      ) : null}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-60 flex-col border-r border-slate-200 bg-white transition-transform md:sticky md:top-0 md:h-screen md:translate-x-0",
          mobileOpen ? "translate-x-0" : "-translate-x-full",
          collapsed && "md:w-[4.5rem]",
        )}
      >
        <div className={cn("flex h-[52px] items-center gap-2 border-b border-slate-200 px-3", collapsed && "md:justify-center md:px-2")}>
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-indigo-700 text-[11px] font-medium text-white">
            L
          </span>
          <span className={cn("min-w-0", collapsed && "md:hidden")}>
            <span className="block text-[13px] font-medium text-slate-900">{brand.name}</span>
            <span className="block truncate text-[11px] text-slate-500">{brand.subtitle}</span>
          </span>
        </div>
        <nav className="flex-1 space-y-4 overflow-y-auto px-2 py-3" aria-label="Primary">
          {navigation.map((section) => (
            <div key={section.label}>
              <p className={cn("px-2.5 pb-1 text-[11px] font-semibold tracking-[0.04em] text-slate-400 uppercase", collapsed && "md:sr-only")}>
                {section.label}
              </p>
              <ul className="space-y-1">
                {section.items.map((item) => {
                  const active = pathname === item.href;
                  const Icon = item.icon;
                  return (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        aria-current={active ? "page" : undefined}
                        aria-label={item.label}
                        title={item.label}
                        onClick={onNavigate}
                        className={cn(
                          "flex h-8 items-center gap-2 rounded-md px-2.5 text-nav text-slate-600 transition-colors hover:bg-slate-50 hover:text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600",
                          active && "bg-indigo-50 text-indigo-800",
                          collapsed && "md:justify-center md:px-0",
                        )}
                      >
                        <Icon className="h-[15px] w-[15px] shrink-0" aria-hidden="true" />
                        <span className={cn(collapsed && "md:sr-only")}>{item.label}</span>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>
        <div className="hidden border-t border-slate-200 p-3 md:block">
          <button
            type="button"
            onClick={onToggleCollapsed}
            className="flex h-8 w-full items-center justify-center gap-2 rounded-md text-secondary text-slate-500 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
            <span className={cn(collapsed && "sr-only")}>Collapse</span>
          </button>
        </div>
      </aside>
    </>
  );
}
