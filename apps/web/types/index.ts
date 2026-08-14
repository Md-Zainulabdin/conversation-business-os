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

export interface SaleItem {
  id: string;
  product_id: string;
  product_name: string;
  quantity: number;
  unit_price: number;
  total_amount: number;
}

export interface Sale {
  id: string;
  customer_id?: string | null;
  customer_name?: string | null;
  total_amount: number;
  sale_date: string;
  notes?: string | null;
  items: SaleItem[];
  created_at: string;
}

export interface PurchaseItem {
  id: string;
  product_id: string;
  product_name: string;
  quantity: number;
  purchase_price: number;
  total_amount: number;
}

export interface Purchase {
  id: string;
  supplier_name: string;
  total_amount: number;
  purchase_date: string;
  notes?: string | null;
  items: PurchaseItem[];
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

export interface ProductCandidate {
  id: string;
  name: string;
  unit: string;
  selling_price: number;
  purchase_price: number;
  stock_quantity: number;
}

export interface AIItem {
  product_name?: string | null;
  quantity?: number | null;
  unit?: string | null;
  unit_price?: number | null;
  total_amount?: number | null;
  product_id?: string | null;
  product_unit?: string | null;
  stock_after?: number | null;
}

export type IssueKind =
  | "not_found"
  | "invalid_unit"
  | "invalid_quantity"
  | "invalid_price"
  | "no_catalog";

export interface ItemIssue {
  kind: IssueKind;
  name: string;
  quantity?: number | null;
  detail?: string | null;
}

export interface AICommand {
  intent: CommandIntent;
  items: AIItem[];
  customer_name?: string | null;
  supplier_name?: string | null;
  title?: string | null;
  category?: string | null;
  notes?: string | null;
  date?: string | null;
  total_amount?: number | null;
}

export interface AIProposalResponse {
  command: AICommand;
  requires_confirmation: boolean;
  message: string;
  disambiguation?: ProductCandidate[] | null;
  issues?: ItemIssue[] | null;
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
  disambiguation?: ProductCandidate[] | null;
  issues?: ItemIssue[] | null;
  busy?: boolean;
  executing?: boolean;
  executed?: boolean;
  cancelled?: boolean;
  error?: boolean;
  errorDetail?: ErrorDetail;
}
