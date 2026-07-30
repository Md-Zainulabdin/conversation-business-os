"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Menu,
  Search,
  Bell,
  LogOut,
  User,
  SlidersHorizontal,
  ChevronDown,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuthStore } from "@/lib/store/auth";

interface HeaderProps {
  onMobileMenuOpen: () => void;
}

export function Header({ onMobileMenuOpen }: HeaderProps) {
  const { user, logout } = useAuthStore();
  const router = useRouter();
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-30 flex h-14 w-full items-center justify-between border-b border-border/80 bg-card/90 px-4 backdrop-blur-xs sm:px-6">
      {/* Left side: Mobile Hamburger & Search input */}
      <div className="flex items-center gap-3 lg:gap-4 flex-1 max-w-md">
        <Button
          variant="ghost"
          size="icon"
          className="lg:hidden h-8 w-8 text-muted-foreground hover:text-foreground shrink-0"
          onClick={onMobileMenuOpen}
          aria-label="Toggle Navigation Menu"
        >
          <Menu className="h-4 w-4" />
        </Button>

        {/* Minimal Search Bar */}
        <div className="relative w-full">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground pointer-events-none" />
          <Input
            type="search"
            placeholder="Search..."
            className="h-8 w-full bg-muted/30 pl-8 pr-3 text-xs shadow-none border-border/60 focus-visible:bg-background"
          />
        </div>
      </div>

      {/* Right side controls */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Notification Bell */}
        <button
          type="button"
          className="relative flex h-8 w-8 items-center justify-center rounded-lg border border-border/80 bg-card text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          aria-label="Notifications"
        >
          <Bell className="h-3.5 w-3.5" />
          <span className="absolute top-1.5 right-1.5 h-1.5 w-1.5 rounded-full bg-emerald-500" />
        </button>

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
