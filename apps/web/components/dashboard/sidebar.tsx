"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Package,
  Tags,
  Users,
  ShoppingBag,
  ShoppingCart,
  Receipt,
  BarChart3,
  Settings,
  Store,
  LogOut,
  Bot,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { useAuthStore } from "@/lib/store/auth";

interface NavItem {
  title: string;
  href: string;
  icon: React.ElementType;
}

interface NavGroup {
  groupLabel: string;
  items: NavItem[];
}

const navGroups: NavGroup[] = [
  {
    groupLabel: "Main",
    items: [
      { title: "Overview", href: "/", icon: LayoutDashboard },
      { title: "Assistant", href: "/assistant", icon: Bot },
    ],
  },
  {
    groupLabel: "Business Operations",
    items: [
      { title: "Products & Stock", href: "/products", icon: Package },
      { title: "Categories", href: "/categories", icon: Tags },
      { title: "Sales", href: "/sales", icon: ShoppingBag },
      { title: "Purchases", href: "/purchases", icon: ShoppingCart },
      { title: "Customers", href: "/customers", icon: Users },
      { title: "Expenses", href: "/expenses", icon: Receipt },
    ],
  },
  {
    groupLabel: "Insights & System",
    items: [
      { title: "Reports", href: "/reports", icon: BarChart3 },
      { title: "Settings", href: "/settings", icon: Settings },
    ],
  },
];

interface SidebarProps {
  onNavClick?: () => void;
  className?: string;
}

export function Sidebar({ onNavClick, className }: SidebarProps) {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();

  return (
    <aside
      className={cn(
        "flex h-full w-64 flex-col justify-between border-r border-border bg-card p-4 transition-all duration-200",
        className
      )}
    >
      <div className="flex flex-col gap-5">
        {/* Minimal Brand Header */}
        <div className="flex items-center justify-between px-2 py-1">
          <Link
            href="/"
            onClick={onNavClick}
            className="flex items-center gap-2.5 group"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-2xs">
              <Store className="h-4 w-4" />
            </div>
            <div className="flex flex-col">
              <span className="font-semibold tracking-tight text-foreground text-sm">
                {user?.store_name || "CBO Dashboard"}
              </span>
              <span className="text-[10px] text-muted-foreground">
                v1.0 • Retail OS
              </span>
            </div>
          </Link>
        </div>

        {/* Categorized Navigation Groups */}
        <nav className="flex flex-col gap-5 px-1 overflow-y-auto">
          {navGroups.map((group, idx) => (
            <div key={idx} className="flex flex-col gap-1">
              <span className="px-2.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/75">
                {group.groupLabel}
              </span>
              <div className="flex flex-col gap-1 mt-0.5">
                {group.items.map((item) => {
                  const isActive =
                    item.href === "/"
                      ? pathname === "/"
                      : pathname.startsWith(item.href);
                  const Icon = item.icon;

                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={onNavClick}
                      className={cn(
                        "flex items-center gap-3 rounded-lg px-2.5 py-1.5 text-xs font-medium transition-colors",
                        isActive
                          ? "bg-secondary text-foreground font-semibold"
                          : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
                      )}
                    >
                      <Icon
                        className={cn(
                          "h-4 w-4 shrink-0",
                          isActive ? "text-foreground" : "text-muted-foreground"
                        )}
                      />
                      <span>{item.title}</span>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </div>

      {/* Clean Bottom User Section */}
      <div className="border-t border-border/80 pt-3 px-1">
        <div className="flex items-center justify-between rounded-lg p-1.5 hover:bg-muted/40 transition-colors">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-secondary border border-border text-foreground font-medium text-xs">
              {user?.name ? user.name.slice(0, 2).toUpperCase() : "US"}
            </div>
            <div className="flex flex-col truncate">
              <span className="text-xs font-medium text-foreground truncate">
                {user?.name || "Retail User"}
              </span>
              <span className="text-[10px] text-muted-foreground truncate">
                {user?.email || "owner@cbo.local"}
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={() => logout()}
            className="text-muted-foreground hover:text-destructive p-1 rounded-md transition-colors"
            title="Sign out"
          >
            <LogOut className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
    </aside>
  );
}
