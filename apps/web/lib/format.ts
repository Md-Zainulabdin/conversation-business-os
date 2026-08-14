import type { AICommand, CommandIntent } from "@/types";

export function formatAmount(value: unknown): string {
  const amount = Number(value);
  if (!Number.isFinite(amount)) return "N/A";
  return `Rs ${amount.toLocaleString("en-PK", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

export const INTENT_LABEL: Record<CommandIntent, string> = {
  sale: "Sale",
  purchase: "Purchase",
  expense: "Expense",
  inquiry: "Inquiry",
  other: "Action",
};

export function commandTotal(command: AICommand): number {
  if (command.intent === "expense") return Number(command.total_amount ?? 0);
  return (command.items ?? []).reduce(
    (sum, item) => sum + Number(item.total_amount ?? 0),
    0
  );
}