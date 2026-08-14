"use client";

import { useState } from "react";
import { Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { cn } from "@/lib/utils";
import { formatAmount } from "@/lib/format";
import type { ProductCandidate } from "@/types";
import {
  CardShell,
  CardHeader,
  CardBody,
  CardFooter,
} from "@/components/assistant/card-shell";

interface ProductSelectProps {
  candidates: ProductCandidate[];
  message: string;
  busy?: boolean;
  onSelect: (productId: string) => void;
}

export function ProductSelect({
  candidates,
  message,
  busy,
  onSelect,
}: ProductSelectProps) {
  const [selected, setSelected] = useState<string | null>(null);

  const icon = (
    <span className="flex size-5 items-center justify-center rounded-full bg-primary text-white">
      <Search className="size-3" />
    </span>
  );

  return (
    <CardShell>
      <CardHeader icon={icon} label="Choose a product" />

      <CardBody>
        <p className="mb-3 text-sm font-medium text-foreground">{message}</p>
        <div
          role="radiogroup"
          aria-label="Select a product"
          className="flex flex-col gap-2"
        >
          {candidates.map((product) => {
            const isSelected = selected === product.id;
            return (
              <label
                key={product.id}
                className={cn(
                  "flex cursor-pointer items-center gap-3 rounded-lg border border-border px-3 py-2.5 transition-colors",
                  isSelected
                    ? "border-primary/60 bg-primary/5 ring-1 ring-primary/20"
                    : "hover:border-primary/40 hover:bg-muted/30"
                )}
              >
                <input
                  type="radio"
                  name="product-choice"
                  value={product.id}
                  checked={isSelected}
                  onChange={() => setSelected(product.id)}
                  className="size-4 shrink-0 accent-primary"
                />
                <span className="flex-1 min-w-0">
                  <span className="block truncate text-sm font-medium text-foreground">
                    {product.name}
                  </span>
                  <span className="block text-xs text-muted-foreground">
                    {product.unit} · {product.stock_quantity} in stock
                  </span>
                </span>
                <span className="shrink-0 text-right">
                  <span className="block text-sm font-semibold text-foreground">
                    {formatAmount(product.selling_price)}
                  </span>
                  <span className="block text-[11px] text-muted-foreground">
                    cost {formatAmount(product.purchase_price)}
                  </span>
                </span>
              </label>
            );
          })}
        </div>
      </CardBody>

      <CardFooter>
        <Button
          size="sm"
          className="flex-1"
          onClick={() => selected && onSelect(selected)}
          disabled={!selected || busy}
        >
          {busy ? <Spinner className="size-3.5" /> : null}
          {busy ? "Checking..." : "Continue"}
        </Button>
      </CardFooter>
    </CardShell>
  );
}