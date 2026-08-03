"use client";

import { Check, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { cn } from "@/lib/utils";
import type { AICommand } from "@/types";
import { INTENT_LABEL, commandRows } from "@/lib/format";

interface CommandCardProps {
  command: AICommand;
  busy?: boolean;
  onExecute: () => void;
  onCancel: () => void;
}

export function CommandCard({
  command,
  busy,
  onExecute,
  onCancel,
}: CommandCardProps) {
  const label = INTENT_LABEL[command.intent];
  const rows = commandRows(command);

  return (
    <div
      className={cn(
        "overflow-hidden rounded-lg border border-border bg-white",
        busy && "opacity-90"
      )}
    >
      <div className="flex items-center justify-between border-b border-border bg-muted/40 px-4 py-2.5">
        <span className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-primary">
          <span className="size-1.5 rounded-full bg-primary" />
          {label}
        </span>
        {busy ? (
          <span className="inline-flex items-center gap-1.5 text-[11px] font-medium text-muted-foreground">
            <Spinner className="size-3" />
            Recording...
          </span>
        ) : (
          <span className="text-[11px] text-muted-foreground">
            Confirm before recording
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-x-8 gap-y-3.5 px-4 py-4 sm:grid-cols-3">
        {rows.map((row) => (
          <div key={row.label} className="min-w-0">
            <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
              {row.label}
            </p>
            <p className="mt-1 text-sm font-medium text-foreground">
              {row.value}
            </p>
          </div>
        ))}
      </div>

      <div className="flex items-center gap-2 border-t border-border px-4 py-3">
        <Button
          size="sm"
          variant="outline"
          className="flex-1"
          onClick={onCancel}
          disabled={busy}
        >
          <X className="size-3.5" />
          Cancel
        </Button>
        <Button
          size="sm"
          variant="default"
          className="flex-1"
          onClick={onExecute}
          disabled={busy}
        >
          {busy ? <Spinner className="size-3.5" /> : <Check className="size-3.5" />}
          {busy ? "Recording..." : "Record"}
        </Button>
      </div>
    </div>
  );
}
