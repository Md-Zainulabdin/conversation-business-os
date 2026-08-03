"use client";

import { AlertTriangle } from "lucide-react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body>
        <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-background p-6 text-center">
          <div className="flex size-12 items-center justify-center rounded-full bg-red-100">
            <AlertTriangle className="size-6 text-red-600" />
          </div>
          <div>
            <h1 className="text-lg font-semibold tracking-tight text-foreground">
              Something went wrong
            </h1>
            <p className="mt-1 max-w-md text-sm text-muted-foreground">
              An unexpected error occurred. Please try reloading the app.
            </p>
            {process.env.NODE_ENV === "development" && error.message && (
              <p className="mt-2 rounded-md bg-muted px-3 py-2 font-mono text-xs text-muted-foreground">
                {error.message}
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={() => reset()}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Try again
          </button>
        </div>
      </body>
    </html>
  );
}