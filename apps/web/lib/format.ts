import type { AICommand, CommandIntent } from "@/types";

function parseDate(value: string | null | undefined): Date | null {
  const date = new Date(value ?? "");
  return Number.isNaN(date.getTime()) ? null : date;
}

export function formatAmount(value: unknown): string {
  const amount = Number(value);
  if (!Number.isFinite(amount)) return "—";
  return `Rs ${amount.toLocaleString("en-PK", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

export function formatDate(value: string | null | undefined): string {
  const date = parseDate(value);
  if (!date) return "—";
  return date.toLocaleDateString("en-PK", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export const INTENT_LABEL: Record<CommandIntent, string> = {
  sale: "Sale",
  purchase: "Purchase",
  expense: "Expense",
  inquiry: "Inquiry",
  other: "Action",
};

export interface CommandRow {
  label: string;
  value: string;
}

export function commandRows(command: AICommand): CommandRow[] {
  const rows: CommandRow[] = [];

  if (command.product_name)
    rows.push({ label: "Product", value: command.product_name });
  if (command.quantity != null)
    rows.push({ label: "Quantity", value: `${command.quantity}` });
  if (command.unit_price != null)
    rows.push({ label: "Unit price", value: formatAmount(command.unit_price) });
  if (command.total_amount != null)
    rows.push({ label: "Total amount", value: formatAmount(command.total_amount) });
  if (command.intent === "sale")
    rows.push({
      label: "Customer",
      value: command.customer_name || "Walk-in customer",
    });
  if (command.intent === "purchase")
    rows.push({
      label: "Supplier",
      value: command.supplier_name || "Unknown supplier",
    });
  if (command.intent === "expense" && command.category)
    rows.push({ label: "Category", value: command.category });
  if (command.title) rows.push({ label: "Title", value: command.title });
  if (command.date) rows.push({ label: "Date", value: formatDate(command.date) });
  if (command.notes) rows.push({ label: "Notes", value: command.notes });

  return rows;
}
