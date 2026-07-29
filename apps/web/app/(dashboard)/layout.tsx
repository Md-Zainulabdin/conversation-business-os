"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LogOut, LayoutDashboard, Tags } from "lucide-react";

import { useAuthStore } from "@/lib/store/auth";

const nav = [
  { label: "Dashboard", href: "/", icon: LayoutDashboard },
  { label: "Categories", href: "/categories", icon: Tags },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { token, user, logout } = useAuthStore();
  const pathname = usePathname();
  const router = useRouter();

  if (!token) {
    return null;
  }

  return (
    <div className="flex min-h-screen bg-background">
      <aside className="flex w-60 flex-col border-r border-border bg-secondary">
        <div className="flex h-12 items-center px-6 border-b border-border">
          <span className="text-sm font-semibold tracking-tight text-foreground">CBO</span>
        </div>

        <nav className="flex-1 space-y-0.5 p-3">
          {nav.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors ${
                  active
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-border p-3">
          <div className="flex items-center justify-between rounded-lg px-3 py-2">
            <span className="text-sm text-muted-foreground truncate">{user?.name}</span>
            <button
              onClick={() => {
                logout();
                router.push("/login");
              }}
              className="rounded-md p-1 text-muted-foreground hover:text-destructive cursor-pointer"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      <main className="flex-1 p-6 overflow-auto">
        {children}
      </main>
    </div>
  );
}
