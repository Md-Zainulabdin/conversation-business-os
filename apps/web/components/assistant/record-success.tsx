"use client";

import { Check } from "lucide-react";

import type { AICommand } from "@/types";
import { commandTotal, formatAmount } from "@/lib/format";
import {
  CardShell,
  CardHeader,
  CardBody,
} from "@/components/assistant/card-shell";

interface RecordSuccessProps {
  label: string;
  command: AICommand;
}

export function RecordSuccess({ label, command }: RecordSuccessProps) {
  const isTrade = command.intent === "sale" || command.intent === "purchase";
  const items = command.items ?? [];
  const total = commandTotal(command);

  const icon = (
    <span className="flex size-5 items-center justify-center rounded-full bg-emerald-500 text-white">
      <Check className="size-3" />
    </span>
  );

  return (
    <CardShell variant="success">
      <CardHeader
        icon={icon}
        label={`${label} recorded`}
        variant="success"
      />

      {isTrade && items.length > 0 ? (
        <CardBody variant="success">
          <ul className="flex flex-col gap-1.5">
            {items.map((item, index) => (
              <li
                key={index}
                className="flex flex-col gap-0.5 text-sm"
              >
                <div className="flex items-baseline justify-between gap-3">
                  <span className="font-medium text-emerald-950">
                    {item.quantity ?? "?"} x{" "}
                    {item.product_name || "Unknown product"}
                  </span>
                  <span className="tabular-nums text-emerald-900">
                    {formatAmount(item.total_amount)}
                  </span>
                </div>
                <div className="flex items-baseline justify-between gap-3 text-xs text-emerald-700">
                  {item.unit_price != null && (
                    <span>
                      {formatAmount(item.unit_price)} per{" "}
                      {item.product_unit || "item"}
                    </span>
                  )}
                  {item.stock_after != null && (
                    <span>
                      Stock left: {item.stock_after} {item.product_unit || ""}
                    </span>
                  )}
                </div>
              </li>
            ))}
          </ul>
          <div className="mt-2 flex items-baseline justify-between gap-3 border-t border-emerald-200 pt-2 text-sm">
            <span className="text-muted-foreground">Total</span>
            <span className="font-semibold tabular-nums text-emerald-950">
              {formatAmount(total)}
            </span>
          </div>
        </CardBody>
      ) : (
        <CardBody variant="success">
          <p className="text-sm font-medium text-emerald-950">
            {command.title || "Recorded."}
          </p>
          <p className="mt-0.5 text-sm tabular-nums text-emerald-700">
            {formatAmount(total)}
          </p>
        </CardBody>
      )}
    </CardShell>
  );
}