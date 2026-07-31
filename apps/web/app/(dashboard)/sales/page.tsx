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

interface Sale {
  id: string;
  customer_name: string | null;
  product_name: string;
  quantity: number;
  unit_price: number;
  total_amount: number;
  sale_date: string;
  notes: string | null;
  created_at: string;
}

export default function SalesPage() {
  const [sales, setSales] = useState<Sale[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [productFilter, setProductFilter] = useState("all");
  const [deleteTarget, setDeleteTarget] = useState<Sale | null>(null);
  const [deleting, setDeleting] = useState(false);

  const debouncedSearch = useDebounce(searchQuery, 200);

  const fetchSales = useCallback(async () => {
    try {
      const data = await api.get<Sale[]>("/sales");
      setSales(data);
    } catch {
      // handled by api.ts
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSales();
  }, [fetchSales]);

  const productOptions = useMemo(
    () => Array.from(new Set(sales.map((s) => s.product_name || "Unspecified"))).sort(),
    [sales]
  );

  const filtered = useMemo(
    () =>
      sales.filter((s) => {
        const q = debouncedSearch.toLowerCase();
        const matchesSearch =
          !q ||
          (s.customer_name || "").toLowerCase().includes(q) ||
          s.product_name.toLowerCase().includes(q) ||
          (s.notes || "").toLowerCase().includes(q);
        const matchesProduct = productFilter === "all" || s.product_name === productFilter;
        return matchesSearch && matchesProduct;
      }),
    [sales, debouncedSearch, productFilter]
  );

  const clearFilters = () => {
    setProductFilter("all");
    setSearchQuery("");
  };

  const filterPills: FilterPill[] = [];
  if (productFilter !== "all") {
    filterPills.push({ label: `Product: ${productFilter}`, onRemove: () => setProductFilter("all") });
  }

  const filters: FilterConfig[] = [
    {
      value: productFilter,
      onChange: setProductFilter,
      options: [
        { label: "All Products", value: "all" },
        ...productOptions.map((p) => ({ label: p, value: p })),
      ],
    },
  ];

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await api.delete(`/sales/${deleteTarget.id}`);
      await fetchSales();
    } catch {
      // handled by api.ts
    }
    setDeleteTarget(null);
    setDeleting(false);
  };

  const columns: Column<Sale>[] = [
    { header: "Customer", render: (s) => <span className="font-medium">{s.customer_name || "Walk-in"}</span> },
    { header: "Product", render: (s) => s.product_name },
    { header: "Qty", align: "right", render: (s) => s.quantity },
    {
      header: "Unit Price",
      align: "right",
      render: (s) => <span className="text-muted-foreground tabular-nums">Rs {Number(s.unit_price).toLocaleString()}</span>,
    },
    {
      header: "Total",
      align: "right",
      render: (s) => <span className="font-medium tabular-nums">Rs {Number(s.total_amount).toLocaleString()}</span>,
    },
    {
      header: "Date",
      render: (s) => (
        <span className="text-muted-foreground tabular-nums">
          {new Date(s.sale_date).toLocaleDateString("en-US", { day: "numeric", month: "short" })}
        </span>
      ),
    },
    {
      header: "Notes",
      render: (s) => <span className="text-muted-foreground max-w-[200px] truncate block">{s.notes || "—"}</span>,
    },
    {
      header: "Action",
      align: "right",
      render: (s) => (
        <div className="flex justify-end gap-3">
          <Link
            href={`/sales/${s.id}/edit`}
            className="rounded p-1 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          >
            <Pencil className="size-3.5" />
          </Link>
          <button
            type="button"
            onClick={() => setDeleteTarget(s)}
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
        title="Sales"
        description="Record customer sales, quantities sold, and total revenues."
        action={
          <Link href="/sales/new">
            <Button size="sm" className="h-8 gap-1.5 text-xs">
              <Plus className="size-3.5" data-icon="inline-start" />
              Record Sale
            </Button>
          </Link>
        }
      />

      <TableToolbar
        searchValue={searchQuery}
        onSearchChange={setSearchQuery}
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
          total={sales.length}
          filteredCount={filtered.length}
          keyExtractor={(s) => s.id}
          emptyMessage="No sales records match your query."
          recordLabel="sales"
        />
      )}

      <Dialog open={!!deleteTarget} onOpenChange={() => setDeleteTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Sale</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this sale of <strong>{deleteTarget?.product_name}</strong>? Stock will be restored.
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
