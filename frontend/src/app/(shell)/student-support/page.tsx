import type { Metadata } from "next";
import { StudentSupportScreen } from "@/components/support/StudentSupportScreen";

export const metadata: Metadata = { title: "Student Support" };

export default function StudentSupportPage() {
  return <StudentSupportScreen />;
}
