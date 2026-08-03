export interface Product {
  id: string;
  name: string;
  sku: string;
  category: string;
  unit: string;
  purchase_price: number;
  selling_price: number;
  stock_quantity: number;
  minimum_stock: number;
  created_at: string;
  updated_at: string;
}

export interface Customer {
  id: string;
  name: string;
  phone: string;
  address?: string;
  created_at: string;
  updated_at: string;
}

export interface Sale {
  id: string;
  customer_id?: string;
  customer_name?: string;
  product_id: string;
  product_name?: string;
  quantity: number;
  unit_price: number;
  total_amount: number;
  sale_date: string;
  notes?: string;
  created_at: string;
}

export interface Purchase {
  id: string;
  product_id: string;
  product_name?: string;
  supplier_name: string;
  quantity: number;
  purchase_price: number;
  total_amount: number;
  purchase_date: string;
  notes?: string;
  created_at: string;
}

export interface Expense {
  id: string;
  title: string;
  category: string;
  amount: number;
  expense_date: string;
  notes?: string;
  created_at: string;
}

export interface Report {
  id: string;
  report_date: string;
  title: string;
  category: string;
  total_sales_count: number;
  total_revenue: number;
  total_expenses: number;
  net_profit: number;
  notes?: string;
  created_at: string;
}

export interface Transaction {
  id: string;
  type: "Sale" | "Purchase" | "Expense";
  reference: string;
  entity: string;
  amount: number;
  status: string;
  date: string;
}

export type CommandIntent = "sale" | "purchase" | "expense" | "inquiry" | "other";

export interface AICommand {
  intent: CommandIntent;
  product_name?: string | null;
  quantity?: number | null;
  unit_price?: number | null;
  total_amount?: number | null;
  customer_name?: string | null;
  supplier_name?: string | null;
  title?: string | null;
  category?: string | null;
  notes?: string | null;
  date?: string | null;
}

export interface AIProposalResponse {
  command: AICommand;
  requires_confirmation: boolean;
  message: string;
}

export interface AIExecuteResponse {
  message: string;
  record: Record<string, unknown>;
}

export interface ErrorDetail {
  title: string;
  hint?: string;
  options?: string[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  command?: AICommand | null;
  requiresConfirmation?: boolean;
  busy?: boolean;
  executing?: boolean;
  executed?: boolean;
  error?: boolean;
  errorDetail?: ErrorDetail;
}
