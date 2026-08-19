"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Menu,
  LogOut,
  User,
  SlidersHorizontal,
  ChevronDown,
  Bell,
  PackageX,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { useAuthStore } from "@/lib/store/auth";
import type { OverviewData } from "@/types";

interface HeaderProps {
  onMobileMenuOpen: () => void;
}

export function Header({ onMobileMenuOpen }: HeaderProps) {
  const { user, logout } = useAuthStore();
  const router = useRouter();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showAlerts, setShowAlerts] = useState(false);
  const [lowStock, setLowStock] = useState<OverviewData["low_stock"]>([]);

  const fetchAlerts = useCallback(async () => {
    try {
      const overview = await api.get<OverviewData>("/stats/overview?period=30d");
      setLowStock(overview.low_stock);
    } catch {
      // handled by api.ts
    }
  }, []);

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 60_000);
    return () => clearInterval(interval);
  }, [fetchAlerts]);

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-30 flex h-14 w-full items-center justify-between border-b border-border/80 bg-card/90 px-4 backdrop-blur-xs sm:px-6">
      {/* Left side: Mobile Hamburger */}
      <div className="flex items-center gap-3 lg:gap-4">
        <Button
          variant="ghost"
          size="icon"
          className="lg:hidden h-8 w-8 text-muted-foreground hover:text-foreground shrink-0"
          onClick={onMobileMenuOpen}
          aria-label="Toggle Navigation Menu"
        >
          <Menu className="h-4 w-4" />
        </Button>
      </div>

      {/* Right side controls */}
      <div className="flex items-center gap-2 sm:gap-3">

        {/* Low Stock Alerts Bell */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowAlerts(!showAlerts)}
            aria-label="Low stock alerts"
            className="relative flex h-8 w-8 items-center justify-center rounded-lg p-1 hover:bg-muted transition-colors text-muted-foreground"
          >
            <Bell className="h-4 w-4" />
            {lowStock.length > 0 && (
              <span className="absolute -top-0.5 -right-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[9px] font-bold text-white">
                {lowStock.length}
              </span>
            )}
          </button>

          {showAlerts && (
            <>
              <div
                className="fixed inset-0 z-40"
                onClick={() => setShowAlerts(false)}
              />
              <div className="absolute right-0 mt-1.5 z-50 w-72 rounded-xl border border-border bg-card p-2 shadow-md text-xs">
                <div className="px-2 py-1.5 border-b border-border/60 mb-1 flex items-center justify-between">
                  <p className="font-medium text-foreground">Low Stock Alerts</p>
                  {lowStock.length > 0 && (
                    <Link
                      href="/products"
                      onClick={() => setShowAlerts(false)}
                      className="text-[10px] font-medium text-primary hover:underline"
                    >
                      View Products
                    </Link>
                  )}
                </div>
                {lowStock.length === 0 ? (
                  <p className="px-2.5 py-4 text-center text-muted-foreground">
                    No low stock items.
                  </p>
                ) : (
                  <div className="max-h-72 overflow-y-auto space-y-0.5">
                    {lowStock.map((p) => (
                      <Link
                        key={p.id}
                        href="/products"
                        onClick={() => setShowAlerts(false)}
                        className="flex items-center gap-2.5 rounded-lg px-2.5 py-2 hover:bg-muted transition-colors"
                      >
                        <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-destructive/10 text-destructive">
                          <PackageX className="h-3 w-3" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="font-medium text-foreground truncate">{p.name}</p>
                          <p className="text-[10px] text-muted-foreground">
                            {p.stock_quantity} left (min {p.minimum_stock})
                          </p>
                        </div>
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {/* User Profile Avatar Pill */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2 rounded-lg p-1 hover:bg-muted transition-colors text-left"
          >
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-secondary border border-border text-foreground font-semibold text-xs uppercase">
              {user?.name ? user.name.slice(0, 2) : "US"}
            </div>
            <span className="hidden sm:inline text-xs font-medium text-foreground">
              {user?.name || "Retail User"}
            </span>
            <ChevronDown className="h-3 w-3 text-muted-foreground hidden sm:block" />
          </button>

          {/* User Menu Dropdown Overlay */}
          {showUserMenu && (
            <>
              <div
                className="fixed inset-0 z-40"
                onClick={() => setShowUserMenu(false)}
              />
              <div className="absolute right-0 mt-1.5 z-50 w-48 rounded-xl border border-border bg-card p-1.5 shadow-md text-xs">
                <div className="px-2.5 py-1.5 border-b border-border/60 mb-1">
                  <p className="font-medium text-foreground truncate">
                    {user?.name || "User"}
                  </p>
                  <p className="text-[10px] text-muted-foreground truncate">
                    {user?.email || "user@cbo.local"}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setShowUserMenu(false);
                    router.push("/settings");
                  }}
                  className="flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 font-medium text-muted-foreground hover:bg-muted hover:text-foreground"
                >
                  <User className="h-3.5 w-3.5" />
                  Account Settings
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowUserMenu(false);
                    router.push("/settings");
                  }}
                  className="flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 font-medium text-muted-foreground hover:bg-muted hover:text-foreground"
                >
                  <SlidersHorizontal className="h-3.5 w-3.5" />
                  Preferences
                </button>
                <div className="my-1 border-t border-border/60" />
                <button
                  type="button"
                  onClick={handleLogout}
                  className="flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 font-medium text-destructive hover:bg-destructive/10"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  Sign Out
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
