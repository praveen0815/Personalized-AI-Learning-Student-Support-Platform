"use client";

import { useEffect, useState } from "react";
import { getHealth } from "@/lib/api/health";

export function ApiHealthNote() {
  const [label, setLabel] = useState("Checking the learning API");

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void getHealth()
        .then((health) => {
          setLabel(`API ${health.status}, database ${health.database}.`);
        })
        .catch(() => {
          setLabel("The learning API health check did not respond.");
        });
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  return <p className="mt-3 font-mono text-meta text-slate-600">{label}</p>;
}
