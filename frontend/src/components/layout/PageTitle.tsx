"use client";

import { useEffect } from "react";
import { useShell } from "@/components/layout/AppShell";

export function PageTitle({ title }: { title: string }) {
  const { setTitle } = useShell();
  useEffect(() => {
    setTitle(title);
  }, [setTitle, title]);
  return null;
}
