"use client";

import { AlertTriangle } from "lucide-react";

import { Button } from "@/components/ui/button";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
      <div className="flex size-12 items-center justify-center rounded-full bg-red-100">
        <AlertTriangle className="size-6 text-red-600" />
      </div>
      <div>
        <h2 className="text-lg font-semibold tracking-tight text-foreground">
          Something went wrong
        </h2>
        <p className="mt-1 max-w-md text-sm text-muted-foreground">
          An unexpected error occurred while loading this page. You can try
          again, or head back to the dashboard.
        </p>
        {process.env.NODE_ENV === "development" && error.message && (
          <p className="mt-2 rounded-md bg-muted px-3 py-2 font-mono text-xs text-muted-foreground">
            {error.message}
          </p>
        )}
      </div>
      <div className="flex items-center gap-2">
        <Button variant="outline" onClick={() => reset()}>
          Try again
        </Button>
        <Button asChild>
          <a href="/">Go to dashboard</a>
        </Button>
      </div>
    </div>
  );
}