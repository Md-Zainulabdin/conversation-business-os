"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuthStore } from "@/lib/store/auth";
import { Sidebar } from "@/components/dashboard/sidebar";
import { Header } from "@/components/dashboard/header";
import { MobileNav } from "@/components/dashboard/mobile-nav";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { token, user, fetchMe } = useAuthStore();
  const router = useRouter();
  const [hydrated, setHydrated] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (hydrated && token && !user) {
      fetchMe();
    }
  }, [hydrated, token, user, fetchMe]);

  useEffect(() => {
    if (hydrated && !token) {
      router.push("/login");
    }
  }, [hydrated, token, router]);

  if (!hydrated || !token) return null;

  return (
    <div className="min-h-screen bg-background font-sans text-foreground flex antialiased">
      {/* Desktop Sidebar (Fixed left) */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:z-40 lg:flex lg:w-64 lg:flex-col">
        <Sidebar />
      </div>

      {/* Mobile Drawer Navigation */}
      <MobileNav
        isOpen={mobileMenuOpen}
        onClose={() => setMobileMenuOpen(false)}
      />

      {/* Main Content Area Wrapper */}
      <div className="flex flex-1 flex-col lg:pl-64 min-w-0 transition-all">
        {/* Top Sticky Header */}
        <Header onMobileMenuOpen={() => setMobileMenuOpen(true)} />

        {/* Main Content View Container */}
        <main className="flex-1 bg-muted/30 p-4 sm:p-6 lg:p-8 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
