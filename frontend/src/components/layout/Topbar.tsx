"use client";

import { useEffect, useRef, useState } from "react";
import { Bell, ChevronDown, Menu, Search } from "lucide-react";
import { brand } from "@/lib/brand";

export function Topbar({ title, onOpenMenu }: { title: string; onOpenMenu: () => void }) {
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [searchNote, setSearchNote] = useState("");
  const notificationsRef = useRef<HTMLDivElement>(null);
  const profileRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onPointerDown(event: MouseEvent) {
      const target = event.target as Node;
      if (notificationsRef.current && !notificationsRef.current.contains(target)) {
        setNotificationsOpen(false);
      }
      if (profileRef.current && !profileRef.current.contains(target)) {
        setProfileOpen(false);
      }
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setNotificationsOpen(false);
        setProfileOpen(false);
      }
    }
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, []);

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="flex h-[52px] items-center gap-2 px-4 md:px-6">
        <button
          type="button"
          className="inline-flex h-8 w-8 items-center justify-center rounded-md text-slate-700 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 md:hidden"
          aria-label="Open navigation"
          onClick={onOpenMenu}
        >
          <Menu className="h-5 w-5" />
        </button>
        <h1 className="min-w-0 flex-1 truncate text-body font-semibold text-slate-900 md:flex-none">{title}</h1>
        <form
          className="relative mx-auto hidden w-[280px] shrink-0 md:block"
          role="search"
          onSubmit={(event) => {
            event.preventDefault();
            setSearchNote("Search is not connected to the learning record yet.");
          }}
        >
          <Search className="pointer-events-none absolute top-1/2 left-2.5 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" aria-hidden="true" />
          <input
            type="search"
            aria-label="Search"
            placeholder="Search"
            className="h-9 w-full rounded-md border border-slate-200 bg-slate-50 pr-3 pl-8 text-body text-slate-900 placeholder:text-secondary placeholder:text-slate-400 focus-visible:border-indigo-600 focus-visible:bg-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600"
          />
        </form>
        <div className="ml-auto flex items-center gap-2">
          <div className="relative" ref={notificationsRef}>
            <button
              type="button"
              className="inline-flex h-8 w-8 items-center justify-center rounded-md text-slate-600 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600"
              aria-label="Notifications"
              aria-expanded={notificationsOpen}
              onClick={() => {
                setNotificationsOpen((open) => !open);
                setProfileOpen(false);
              }}
            >
              <Bell className="h-4 w-4" aria-hidden="true" />
            </button>
            {notificationsOpen ? (
              <div className="absolute right-0 mt-2 w-56 rounded-lg border border-slate-200 bg-white p-3 text-body shadow-sm">
                <p className="font-medium text-slate-900">No notifications</p>
                <p className="mt-1 text-secondary text-slate-500">New learning updates will appear here.</p>
              </div>
            ) : null}
          </div>
          <div className="relative" ref={profileRef}>
            <button
              type="button"
              className="inline-flex h-8 items-center gap-2 rounded-md px-1.5 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600"
              aria-label={`${brand.studentLabel} menu`}
              aria-expanded={profileOpen}
              onClick={() => {
                setProfileOpen((open) => !open);
                setNotificationsOpen(false);
              }}
            >
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-900 text-[11px] font-medium text-white">
                S
              </span>
              <span className="hidden text-left sm:block">
                <span className="block text-secondary font-medium text-slate-900">{brand.studentLabel}</span>
                <span className="block text-[11px] text-slate-500">{brand.studentRole}</span>
              </span>
              <ChevronDown className="hidden h-4 w-4 text-slate-400 sm:block" aria-hidden="true" />
            </button>
            {profileOpen ? (
              <div className="absolute right-0 mt-2 w-48 rounded-lg border border-slate-200 bg-white p-3 text-body shadow-sm">
                <p className="font-medium text-slate-900">{brand.studentLabel}</p>
                <p className="mt-1 text-secondary text-slate-500">{brand.studentRole}</p>
              </div>
            ) : null}
          </div>
        </div>
      </div>
      <form
        className="px-4 pb-3 md:hidden"
        role="search"
        onSubmit={(event) => {
          event.preventDefault();
          setSearchNote("Search is not connected to the learning record yet.");
        }}
      >
        <label className="sr-only" htmlFor="mobile-search">
          Search
        </label>
        <input
          id="mobile-search"
          type="search"
          placeholder="Search"
          className="h-9 w-full rounded-md border border-slate-200 bg-slate-50 px-3 text-body placeholder:text-secondary focus-visible:border-indigo-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600"
        />
      </form>
      {searchNote ? (
        <p className="px-4 pb-2 text-meta text-slate-500 md:px-6" role="status">
          {searchNote}
        </p>
      ) : null}
    </header>
  );
}
