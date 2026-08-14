"use client";

import { PageHeader } from "@/components/shared/page-header";

export default function ReportsPage() {
  return (
    <div className="mx-auto max-w-7xl space-y-5">
      <PageHeader
        title="Reports & Analytics"
        description="Daily sales summaries, gross revenue metrics, and inventory health audits."
      />

      <div className="rounded-lg border border-dashed bg-card p-10 text-center">
        <h2 className="text-base font-semibold text-foreground">
          Reports are on the way
        </h2>
        <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">
          Daily summaries, revenue breakdowns, and low-stock alerts will appear
          here in a future update.
        </p>
      </div>
    </div>
  );
}