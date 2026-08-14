"use client";

import { AlertTriangle } from "lucide-react";

import {
  CardShell,
  CardHeader,
  CardBody,
} from "@/components/assistant/card-shell";

interface ErrorNoticeProps {
  title: string;
  hint?: string;
  options?: string[];
}

export function ErrorNotice({ title, hint, options }: ErrorNoticeProps) {
  const icon = (
    <span className="flex size-5 items-center justify-center rounded-full bg-red-500 text-white">
      <AlertTriangle className="size-3" />
    </span>
  );

  return (
    <CardShell variant="error">
      <CardHeader
        icon={icon}
        label="Couldn&apos;t record"
        variant="error"
      />

      <CardBody variant="error">
        <p className="text-sm font-medium text-red-900">{title}</p>
        {hint && <p className="mt-1 text-sm text-red-700">{hint}</p>}
        {options && options.length > 0 && (
          <ul className="mt-2 flex flex-col gap-1.5">
            {options.map((opt) => (
              <li key={opt} className="text-sm text-red-700">
                {opt}
              </li>
            ))}
          </ul>
        )}
      </CardBody>
    </CardShell>
  );
}