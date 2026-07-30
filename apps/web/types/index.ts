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

export interface SettingItem {
  id: string;
  setting: string;
  value: string;
  category: string;
  updated_at: string;
}
