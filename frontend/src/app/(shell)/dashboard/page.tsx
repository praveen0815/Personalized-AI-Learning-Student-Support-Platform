import type { Metadata } from "next";
import { DashboardScreen } from "@/components/dashboard/DashboardScreen";

export const metadata: Metadata = {
  title: "Dashboard",
};

export default function DashboardPage() {
  return <DashboardScreen />;
}
