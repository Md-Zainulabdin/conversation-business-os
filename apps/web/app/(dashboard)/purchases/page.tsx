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

import type { Purchase } from "@/types";

type PurchaseRow = Purchase;

export default function PurchasesPage() {
  const [purchases, setPurchases] = useState<Purchase[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [supplierFilter, setSupplierFilter] = useState("all");
  const [deleteTarget, setDeleteTarget] = useState<Purchase | null>(null);
  const [deleting, setDeleting] = useState(false);

  const debouncedSearch = useDebounce(searchQuery, 200);

  const fetchPurchases = useCallback(async () => {
    try {
      const data = await api.get<Purchase[]>("/purchases");
      setPurchases(data);
    } catch {
      // handled by api.ts
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPurchases();
  }, [fetchPurchases]);

  const supplierOptions = useMemo(
    () => Array.from(new Set(purchases.map((p) => p.supplier_name))).sort(),
    [purchases]
  );

  const filtered = useMemo(
    () =>
      purchases.filter((p) => {
        const q = debouncedSearch.toLowerCase();
        const names = p.items.map((i) => i.product_name).join(" ");
        const matchesSearch =
          !q ||
          p.supplier_name.toLowerCase().includes(q) ||
          names.toLowerCase().includes(q) ||
          (p.notes || "").toLowerCase().includes(q);
        const matchesSupplier = supplierFilter === "all" || p.supplier_name === supplierFilter;
        return matchesSearch && matchesSupplier;
      }),
    [purchases, debouncedSearch, supplierFilter]
  );

  const clearFilters = () => {
    setSupplierFilter("all");
    setSearchQuery("");
  };

  const filterPills: FilterPill[] = [];
  if (supplierFilter !== "all") {
    filterPills.push({ label: `Supplier: ${supplierFilter}`, onRemove: () => setSupplierFilter("all") });
  }

  const filters: FilterConfig[] = [
    {
      value: supplierFilter,
      onChange: setSupplierFilter,
      options: [
        { label: "All Suppliers", value: "all" },
        ...supplierOptions.map((s) => ({ label: s, value: s })),
      ],
    },
  ];

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await api.delete(`/purchases/${deleteTarget.id}`);
      await fetchPurchases();
    } catch {
      // handled by api.ts
    }
    setDeleteTarget(null);
    setDeleting(false);
  };

  const columns: Column<PurchaseRow>[] = [
    { header: "Supplier", render: (p) => <span className="font-medium">{p.supplier_name}</span> },
    {
      header: "Products",
      render: (p) => {
        const names = p.items.map((i) => i.product_name);
        const text =
          names.length > 2 ? `${names.slice(0, 2).join(", ")} +${names.length - 2} more` : names.join(", ");
        return <span className="block max-w-[260px] truncate">{text || "N/A"}</span>;
      },
    },
    {
      header: "Total Qty",
      align: "right",
      render: (p) => p.items.reduce((sum, i) => sum + i.quantity, 0),
    },
    {
      header: "Total",
      align: "right",
      render: (p) => <span className="font-medium tabular-nums">Rs {Number(p.total_amount).toLocaleString()}</span>,
    },
    {
      header: "Date",
      render: (p) => (
        <span className="text-muted-foreground tabular-nums">
          {new Date(p.purchase_date).toLocaleDateString("en-US", { day: "numeric", month: "short" })}
        </span>
      ),
    },
    {
      header: "Notes",
      render: (p) => <span className="text-muted-foreground max-w-[200px] truncate block">{p.notes || "No notes"}</span>,
    },
    {
      header: "Action",
      align: "right",
      render: (p) => (
        <div className="flex justify-end gap-3">
          <Link
            href={`/purchases/${p.id}/edit`}
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
        title="Purchases"
        description="Track inventory restocks from suppliers to increase stock levels."
        action={
          <Link href="/purchases/new">
            <Button size="sm" className="h-8 gap-1.5 text-xs">
              <Plus className="size-3.5" data-icon="inline-start" />
              Record Purchase
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
          total={purchases.length}
          filteredCount={filtered.length}
          keyExtractor={(p) => p.id}
          emptyMessage="No purchases match your query."
          recordLabel="purchases"
        />
      )}

      <Dialog open={!!deleteTarget} onOpenChange={() => setDeleteTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Purchase</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this purchase
              {deleteTarget && deleteTarget.items.length > 0 && (
                <> of <strong>{deleteTarget.items.map((i) => i.product_name).join(", ")}</strong></>
              )}
              ? Stock will be reduced.
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
