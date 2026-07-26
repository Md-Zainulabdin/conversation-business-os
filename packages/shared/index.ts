export interface Product {
  id: string;
  name: string;
  sku: string;
  price: number;
  quantity: number;
  category_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface Sale {
  id: string;
  product_id: string;
  quantity: number;
  total: number;
  created_at: string;
}
