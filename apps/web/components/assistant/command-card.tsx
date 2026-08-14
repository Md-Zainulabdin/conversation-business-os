"use client";

import { Check, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { cn } from "@/lib/utils";
import type { AICommand, ItemIssue, IssueKind } from "@/types";
import { INTENT_LABEL, commandTotal, formatAmount } from "@/lib/format";
import {
  CardShell,
  CardHeader,
  CardBody,
  CardFooter,
} from "@/components/assistant/card-shell";

interface CommandCardProps {
  command: AICommand;
  busy?: boolean;
  cancelled?: boolean;
  blocked?: boolean;
  issues?: ItemIssue[] | null;
  onExecute: () => void;
  onCancel: () => void;
}

const ISSUE_TEXT: Record<IssueKind, string> = {
  not_found: "not in your catalog",
  invalid_unit: "wrong unit",
  invalid_quantity: "missing quantity",
  invalid_price: "invalid price",
  no_catalog: "no products yet",
};

export function CommandCard({
  command,
  busy,
  cancelled,
  blocked,
  issues,
  onExecute,
  onCancel,
}: CommandCardProps) {
  const label = INTENT_LABEL[command.intent];
  const items = command.items ?? [];
  const isTrade = command.intent === "sale" || command.intent === "purchase";
  const total = commandTotal(command);
  const skipped = issues ?? [];

  const variant = blocked ? "error" : "default";

  const iconBg = cancelled
    ? "bg-muted-foreground"
    : blocked
      ? "bg-destructive"
      : "bg-primary";

  const icon = (
    <span
      className={cn(
        "flex size-5 items-center justify-center rounded-full text-white",
        iconBg
      )}
    >
      <X className="size-3" />
    </span>
  );

  let trailing: React.ReactNode = null;
  if (busy) {
    trailing = (
      <span className="inline-flex items-center gap-1.5 text-[11px] font-medium text-muted-foreground">
        <Spinner className="size-3" />
        Recording...
      </span>
    );
  } else if (cancelled) {
    trailing = (
      <span className="text-[11px] font-medium text-muted-foreground">
        Cancelled
      </span>
    );
  } else if (blocked) {
    trailing = (
      <span className="text-[11px] font-semibold uppercase tracking-wide text-destructive">
        Can&apos;t record
      </span>
    );
  } else {
    trailing = (
      <span className="text-[11px] text-muted-foreground">Confirm</span>
    );
  }

  return (
    <CardShell
      variant={variant}
      className={cn(
        busy && "opacity-90",
        cancelled && "border-muted bg-muted/20"
      )}
    >
      <CardHeader
        icon={icon}
        label={label}
        variant={variant}
        trailing={trailing}
        className={cn(cancelled && "bg-muted/30")}
      />

      {isTrade && items.length > 0 && (
        <CardBody
          variant={variant}
          className={cn(cancelled && "opacity-70")}
        >
          <ul className="flex flex-col gap-1.5">
            {items.map((item, index) => (
              <li
                key={index}
                className="flex flex-col gap-0.5 text-sm"
              >
                <div className="flex items-baseline justify-between gap-3">
                  <span className="font-medium text-foreground">
                    {item.quantity ?? "?"} x{" "}
                    {item.product_name || "Unknown product"}
                  </span>
                  <span className="tabular-nums text-muted-foreground">
                    {formatAmount(item.total_amount)}
                  </span>
                </div>
                {item.unit_price != null && (
                  <span className="text-xs text-muted-foreground">
                    {formatAmount(item.unit_price)} per{" "}
                    {item.product_unit || "item"}
                  </span>
                )}
              </li>
            ))}
          </ul>
          <div className="mt-2 flex items-baseline justify-between gap-3 border-t border-border pt-2 text-sm">
            <span className="text-muted-foreground">Total</span>
            <span className="font-semibold tabular-nums text-foreground">
              {formatAmount(total)}
            </span>
          </div>
          {!cancelled &&
            (command.customer_name || command.supplier_name) && (
              <p className="mt-2 text-xs text-muted-foreground">
                {command.intent === "sale"
                  ? `Customer: ${command.customer_name || "Walk-in"}`
                  : `Supplier: ${command.supplier_name || "Unknown"}`}
              </p>
            )}
        </CardBody>
      )}

      {command.intent === "expense" && (
        <CardBody
          variant={variant}
          className={cn(cancelled && "opacity-70")}
        >
          <p className="text-sm font-medium text-foreground">
            {command.title || "Expense"}
          </p>
          <p className="mt-0.5 text-sm tabular-nums text-muted-foreground">
            {formatAmount(total)}
          </p>
        </CardBody>
      )}

      {skipped.length > 0 && (
        <CardBody
          variant="error"
          className={cn(cancelled && "bg-muted/20")}
        >
          <ul className="flex flex-col gap-1.5">
            {skipped.map((issue, index) => (
              <li key={index} className="text-sm">
                <span className="font-medium text-foreground">
                  {issue.name}
                </span>
                {issue.quantity ? ` (x${issue.quantity})` : ""}{" "}
                <span className="text-muted-foreground">
                  {ISSUE_TEXT[issue.kind] ?? issue.kind}
                </span>
              </li>
            ))}
          </ul>
        </CardBody>
      )}

      {cancelled ? null : blocked ? (
        <CardFooter className="justify-center bg-muted/20">
          <span className="text-xs font-medium text-muted-foreground">
            Nothing was recorded. Add the missing items to your catalog first.
          </span>
        </CardFooter>
      ) : (
        <CardFooter>
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
        </CardFooter>
      )}
    </CardShell>
  );
}