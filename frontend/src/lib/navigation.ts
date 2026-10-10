import {
  AlertTriangle,
  BookOpen,
  Bot,
  ClipboardCheck,
  HandHeart,
  LayoutDashboard,
  Library,
  Settings,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";

export type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
};

export type NavSection = {
  label: string;
  items: NavItem[];
};

export const navigation: NavSection[] = [
  {
    label: "Main",
    items: [
      { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
      { href: "/courses", label: "My Courses", icon: BookOpen },
      { href: "/tutor", label: "AI Tutor", icon: Bot },
      { href: "/assessments", label: "Assessments", icon: ClipboardCheck },
    ],
  },
  {
    label: "Learning",
    items: [
      { href: "/progress", label: "Progress", icon: TrendingUp },
      { href: "/learning-gaps", label: "Learning Gaps", icon: AlertTriangle },
      { href: "/knowledge", label: "Knowledge Base", icon: Library },
    ],
  },
  {
    label: "Support",
    items: [{ href: "/student-support", label: "Student Support", icon: HandHeart }],
  },
  {
    label: "System",
    items: [{ href: "/settings", label: "Settings", icon: Settings }],
  },
];
