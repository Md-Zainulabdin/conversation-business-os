import { api } from "@/lib/api";

export interface Category {
  id: number;
  name: string;
  description: string | null;
  color: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CategoryCreate {
  name: string;
  description?: string | null;
  color?: string | null;
  is_active?: boolean;
}

export interface CategoryUpdate {
  name?: string | null;
  description?: string | null;
  color?: string | null;
  is_active?: boolean | null;
}

export const categoriesApi = {
  list: () => api.get<Category[]>("/categories/"),
  get: (id: number) => api.get<Category>(`/categories/${id}`),
  create: (data: CategoryCreate) => api.post<Category>("/categories/", data),
  update: (id: number, data: CategoryUpdate) =>
    api.put<Category>(`/categories/${id}`, data),
  remove: (id: number) => api.delete(`/categories/${id}`),
};
