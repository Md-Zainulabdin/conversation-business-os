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

interface Expense {
  id: string;
  title: string;
  category: string;
  amount: number;
  expense_date: string;
  notes: string | null;
  created_at: string;
}

const expenseCategories = ["Electricity", "Internet", "Transport", "Salary", "Miscellaneous"];

export default function ExpensesPage() {
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [deleteTarget, setDeleteTarget] = useState<Expense | null>(null);
  const [deleting, setDeleting] = useState(false);

  const debouncedSearch = useDebounce(searchQuery, 200);

  const fetchExpenses = useCallback(async () => {
    try {
      const data = await api.get<Expense[]>("/expenses");
      setExpenses(data);
    } catch {
      // handled by api.ts
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchExpenses();
  }, [fetchExpenses]);

  const filtered = useMemo(
    () =>
      expenses.filter((e) => {
        const q = debouncedSearch.toLowerCase();
        const matchesSearch =
          !q ||
          e.title.toLowerCase().includes(q) ||
          e.category.toLowerCase().includes(q) ||
          (e.notes || "").toLowerCase().includes(q);
        const matchesCategory = categoryFilter === "all" || e.category === categoryFilter;
        return matchesSearch && matchesCategory;
      }),
    [expenses, debouncedSearch, categoryFilter]
  );

  const clearFilters = () => {
    setCategoryFilter("all");
    setSearchQuery("");
  };

  const filterPills: FilterPill[] = [];
  if (categoryFilter !== "all") {
    filterPills.push({ label: `Category: ${categoryFilter}`, onRemove: () => setCategoryFilter("all") });
  }

  const filters: FilterConfig[] = [
    {
      value: categoryFilter,
      onChange: setCategoryFilter,
      options: [
        { label: "All Categories", value: "all" },
        ...expenseCategories.map((c) => ({ label: c, value: c })),
      ],
    },
  ];

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await api.delete(`/expenses/${deleteTarget.id}`);
      await fetchExpenses();
    } catch {
      // handled by api.ts
    }
    setDeleteTarget(null);
    setDeleting(false);
  };

  const columns: Column<Expense>[] = [
    {
      header: "Expense Title",
      render: (e) => (
        <Link href={`/expenses/${e.id}/edit`} className="font-medium hover:text-primary transition-colors">
          {e.title}
        </Link>
      ),
    },
    { header: "Category", render: (e) => e.category },
    {
      header: "Amount",
      align: "right",
      render: (e) => <span className="font-medium tabular-nums">Rs {Number(e.amount).toLocaleString()}</span>,
    },
    {
      header: "Date",
      render: (e) => (
        <span className="text-muted-foreground tabular-nums">
          {new Date(e.expense_date).toLocaleDateString("en-US", { day: "numeric", month: "short" })}
        </span>
      ),
    },
    {
      header: "Notes",
      render: (e) => <span className="text-muted-foreground max-w-[280px] truncate block">{e.notes || "No notes"}</span>,
    },
    {
      header: "Action",
      align: "right",
      render: (e) => (
        <div className="flex justify-end gap-3">
          <Link
            href={`/expenses/${e.id}/edit`}
            className="rounded p-1 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          >
            <Pencil className="size-3.5" />
          </Link>
          <button
            type="button"
            onClick={() => setDeleteTarget(e)}
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
        title="Expenses"
        description="Track operating costs such as electricity, internet, transport, and salaries."
        action={
          <Link href="/expenses/new">
            <Button size="sm" className="h-8 gap-1.5 text-xs">
              <Plus className="size-3.5" data-icon="inline-start" />
              Add Expense
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
          total={expenses.length}
          filteredCount={filtered.length}
          keyExtractor={(e) => e.id}
          emptyMessage="No expenses match your criteria."
          recordLabel="expenses"
        />
      )}

      <Dialog open={!!deleteTarget} onOpenChange={() => setDeleteTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Expense</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete <strong>{deleteTarget?.title}</strong>? This action cannot be undone.
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
