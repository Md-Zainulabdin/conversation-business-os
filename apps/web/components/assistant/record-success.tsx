"use client";

import { Check } from "lucide-react";

interface RecordSuccessProps {
  label: string;
  message: string;
}

export function RecordSuccess({ label, message }: RecordSuccessProps) {
  return (
    <div className="overflow-hidden rounded-lg border border-emerald-200 bg-emerald-50">
      <div className="flex items-center gap-2 border-b border-emerald-200 px-4 py-2.5">
        <span className="flex size-5 items-center justify-center rounded-full bg-emerald-500 text-white">
          <Check className="size-3" />
        </span>
        <span className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
          {label} recorded
        </span>
      </div>
      <p className="px-4 py-3 text-sm text-emerald-900">{message}</p>
    </div>
  );
}
