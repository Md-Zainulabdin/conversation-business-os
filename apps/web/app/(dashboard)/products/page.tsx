"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Plus, Pencil, Trash2 } from "lucide-react";

import { api } from "@/lib/api";
import { useDebounce } from "@/lib/hooks/use-debounce";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Spinner } from "@/components/ui/spinner";
import { PageHeader } from "@/components/shared/page-header";
import { DataTable, type Column } from "@/components/shared/data-table";
import { TableToolbar, type FilterConfig, type FilterPill } from "@/components/shared/table-toolbar";

interface Product {
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

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [stockFilter, setStockFilter] = useState("all");
  const [deleteTarget, setDeleteTarget] = useState<Product | null>(null);
  const [deleting, setDeleting] = useState(false);

  const debouncedSearch = useDebounce(searchQuery, 200);

  const fetchProducts = useCallback(async () => {
    try {
      const [productsData, categoriesData] = await Promise.all([
        api.get<Product[]>("/products"),
        api.get<{ id: string; name: string }[]>("/categories"),
      ]);
      setProducts(productsData);
      const uniqueCategories = [...new Set(productsData.map((p) => p.category))].sort();
      setCategories(uniqueCategories);
    } catch {
      // handled by api.ts
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  const filtered = useMemo(
    () =>
      products.filter((p) => {
        const q = debouncedSearch.toLowerCase();
        const matchesSearch =
          !q ||
          p.name.toLowerCase().includes(q) ||
          p.sku.toLowerCase().includes(q) ||
          p.category.toLowerCase().includes(q);
        const matchesCategory = categoryFilter === "all" || p.category === categoryFilter;
        const matchesStock =
          stockFilter === "all" ||
          (stockFilter === "low" && p.stock_quantity <= p.minimum_stock) ||
          (stockFilter === "in" && p.stock_quantity > p.minimum_stock);
        return matchesSearch && matchesCategory && matchesStock;
      }),
    [products, debouncedSearch, categoryFilter, stockFilter]
  );

  const clearFilters = () => {
    setCategoryFilter("all");
    setStockFilter("all");
    setSearchQuery("");
  };

  const filterPills: FilterPill[] = [];
  if (categoryFilter !== "all") {
    filterPills.push({ label: `Category: ${categoryFilter}`, onRemove: () => setCategoryFilter("all") });
  }
  if (stockFilter !== "all") {
    filterPills.push({ label: `Stock: ${stockFilter === "low" ? "Low Stock" : "In Stock"}`, onRemove: () => setStockFilter("all") });
  }

  const filters: FilterConfig[] = [
    {
      value: categoryFilter,
      onChange: setCategoryFilter,
      options: [
        { label: "All Categories", value: "all" },
        ...categories.map((c) => ({ label: c, value: c })),
      ],
    },
    {
      value: stockFilter,
      onChange: setStockFilter,
      options: [
        { label: "All Stock", value: "all" },
        { label: "Low Stock", value: "low" },
        { label: "In Stock", value: "in" },
      ],
    },
  ];

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await api.delete(`/products/${deleteTarget.id}`);
      await fetchProducts();
    } catch {
      // handled by api.ts
    }
    setDeleteTarget(null);
    setDeleting(false);
  };

  const columns: Column<Product>[] = [
    {
      header: "Name",
      render: (p) => (
        <Link href={`/products/${p.id}/edit`} className="font-medium hover:text-primary transition-colors">
          {p.name}
        </Link>
      ),
    },
    { header: "SKU", render: (p) => <span className="text-muted-foreground text-xs font-mono">{p.sku}</span> },
    {
      header: "Category",
      render: (p) => (
        <span className="inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium ring-1 ring-inset bg-muted text-muted-foreground ring-border">
          {p.category}
        </span>
      ),
    },
    { header: "Unit", render: (p) => <span className="text-muted-foreground">{p.unit}</span> },
    {
      header: "Cost",
      align: "right",
      render: (p) => (
        <span className="tabular-nums text-muted-foreground">
          Rs {Number(p.purchase_price).toLocaleString()}
        </span>
      ),
    },
    {
      header: "Price",
      align: "right",
      render: (p) => (
        <span className="tabular-nums font-medium">
          Rs {Number(p.selling_price).toLocaleString()}
        </span>
      ),
    },
    {
      header: "Stock",
      align: "right",
      render: (p) => {
        const low = p.stock_quantity <= p.minimum_stock;
        return (
          <span
            className={`tabular-nums font-medium ${low ? "text-destructive" : "text-foreground"}`}
          >
            {p.stock_quantity}
          </span>
        );
      },
    },
    {
      header: "Action",
      align: "right",
      render: (p) => (
        <div className="flex justify-end gap-3">
          <Link
            href={`/products/${p.id}/edit`}
            className="rounded p-1 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          >
            <Pencil className="size-3.5" />
          </Link>
          <button
            type="button"
            onClick={() => setDeleteTarget(p)}
            className="rounded p-1 text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
          >
            <Trash2 className="size-3.5" />
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="mx-auto max-w-7xl space-y-5">
      <PageHeader
        title="Products & Stock"
        description="Manage your products and stock."
        action={
          <Link href="/products/new">
            <Button size="sm" className="h-8 gap-1.5 text-xs">
              <Plus className="size-3.5" data-icon="inline-start" />
              Add Product
            </Button>
          </Link>
        }
      />

      <TableToolbar
        searchValue={searchQuery}
        onSearchChange={setSearchQuery}
        searchPlaceholder="Search"
        filters={filters}
        filterPills={filterPills}
        onClearFilters={clearFilters}
      />

      {loading ? (
        <div className="flex justify-center py-10">
          <Spinner className="size-5" />
        </div>
      ) : (
        <DataTable
          columns={columns}
          data={filtered}
          total={products.length}
          filteredCount={filtered.length}
          keyExtractor={(p) => p.id}
          emptyMessage="No products yet."
          recordLabel="products"
        />
      )}

      <Dialog open={!!deleteTarget} onOpenChange={() => setDeleteTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Product</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete <strong>{deleteTarget?.name}</strong>? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" size="sm" onClick={() => setDeleteTarget(null)} disabled={deleting}>
              Cancel
            </Button>
            <Button variant="destructive" size="sm" onClick={handleDelete} disabled={deleting}>
              {deleting && <Spinner data-icon="inline-start" />}
              {deleting ? "Deleting" : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
