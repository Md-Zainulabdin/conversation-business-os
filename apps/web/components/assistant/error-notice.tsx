"use client";

import { AlertTriangle } from "lucide-react";

interface ErrorNoticeProps {
  title: string;
  hint?: string;
  options?: string[];
}

export function ErrorNotice({ title, hint, options }: ErrorNoticeProps) {
  return (
    <div className="max-w-2xl overflow-hidden rounded-lg border border-red-200 bg-red-50">
      <div className="flex items-center gap-2 border-b border-red-200 px-4 py-2.5">
        <span className="flex size-5 items-center justify-center rounded-full bg-red-500 text-white">
          <AlertTriangle className="size-3" />
        </span>
        <span className="text-xs font-semibold uppercase tracking-wide text-red-700">
          Couldn&apos;t process
        </span>
      </div>
      <p className="px-4 py-3 text-sm font-medium text-red-900">{title}</p>
      {hint && <p className="px-4 pb-3 text-xs text-red-700">{hint}</p>}
      {options && options.length > 0 && (
        <ul className="space-y-1.5 px-4 pb-3.5">
          {options.map((opt) => (
            <li key={opt} className="flex items-center gap-2 text-xs text-red-700">
              <span className="size-1 shrink-0 rounded-full bg-red-400" />
              <span>{opt}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
