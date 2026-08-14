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
import { TableToolbar } from "@/components/shared/table-toolbar";

interface Category {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export default function CategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<Category | null>(null);
  const [deleting, setDeleting] = useState(false);

  const debouncedSearch = useDebounce(searchQuery, 200);

  const fetchCategories = useCallback(async () => {
    try {
      const data = await api.get<Category[]>("/categories");
      setCategories(data);
    } catch {
      // handled by api.ts
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

  const filtered = useMemo(
    () =>
      categories.filter((c) => {
        if (!debouncedSearch) return true;
        const q = debouncedSearch.toLowerCase();
        return c.name.toLowerCase().includes(q) || (c.description ?? "").toLowerCase().includes(q);
      }),
    [categories, debouncedSearch]
  );

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await api.delete(`/categories/${deleteTarget.id}`);
      await fetchCategories();
    } catch {
      // handled by api.ts
    }
    setDeleteTarget(null);
    setDeleting(false);
  };

  const columns: Column<Category>[] = [
    {
      header: "Name",
      render: (c) => (
        <Link href={`/categories/${c.id}/edit`} className="font-medium hover:text-primary transition-colors">
          {c.name}
        </Link>
      ),
    },
    {
      header: "Description",
      render: (c) => (
        <span className="text-muted-foreground">{c.description || "No description"}</span>
      ),
    },
    {
      header: "Action",
      align: "right",
      render: (c) => (
        <div className="flex justify-end gap-3">
          <Link
            href={`/categories/${c.id}/edit`}
            className="rounded p-1 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          >
            <Pencil className="size-3.5" />
          </Link>
          <button
            type="button"
            onClick={() => setDeleteTarget(c)}
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
        title="Categories"
        description="Organize your products into categories."
        action={
          <Link href="/categories/new">
            <Button size="sm" className="h-8 gap-1.5 text-xs">
              <Plus className="size-3.5" data-icon="inline-start" />
              Add Category
            </Button>
          </Link>
        }
      />

      <TableToolbar
        searchValue={searchQuery}
        onSearchChange={setSearchQuery}
        searchPlaceholder="Search"
      />

      {loading ? (
        <div className="flex justify-center py-10">
          <Spinner className="size-5" />
        </div>
      ) : (
        <DataTable
          columns={columns}
          data={filtered}
          total={categories.length}
          filteredCount={filtered.length}
          keyExtractor={(c) => c.id}
          emptyMessage="No categories yet."
          recordLabel="categories"
        />
      )}

      <Dialog open={!!deleteTarget} onOpenChange={() => setDeleteTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Category</DialogTitle>
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
