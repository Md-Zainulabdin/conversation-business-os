"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Plus, Pencil, Trash2, MapPin } from "lucide-react";

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

interface Customer {
  id: string;
  name: string;
  phone: string;
  address: string | null;
  created_at: string;
  updated_at: string;
}

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [fieldFilter, setFieldFilter] = useState("all");
  const [deleteTarget, setDeleteTarget] = useState<Customer | null>(null);
  const [deleting, setDeleting] = useState(false);

  const debouncedSearch = useDebounce(searchQuery, 200);

  const fetchCustomers = useCallback(async () => {
    try {
      const data = await api.get<Customer[]>("/customers");
      setCustomers(data);
    } catch {
      // handled by api.ts
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCustomers();
  }, [fetchCustomers]);

  const filtered = useMemo(
    () =>
      customers.filter((c) => {
        const q = debouncedSearch.toLowerCase();
        if (!q) return true;
        if (fieldFilter === "name") return c.name.toLowerCase().includes(q);
        if (fieldFilter === "phone") return c.phone.toLowerCase().includes(q);
        if (fieldFilter === "address") return (c.address || "").toLowerCase().includes(q);
        return (
          c.name.toLowerCase().includes(q) ||
          c.phone.toLowerCase().includes(q) ||
          (c.address || "").toLowerCase().includes(q)
        );
      }),
    [customers, debouncedSearch, fieldFilter]
  );

  const clearFilters = () => {
    setFieldFilter("all");
    setSearchQuery("");
  };

  const filterPills: FilterPill[] = [];
  if (fieldFilter !== "all") {
    const labels: Record<string, string> = { name: "Name", phone: "Phone", address: "Address" };
    filterPills.push({ label: `Field: ${labels[fieldFilter]}`, onRemove: () => setFieldFilter("all") });
  }

  const filters: FilterConfig[] = [
    {
      value: fieldFilter,
      onChange: setFieldFilter,
      options: [
        { label: "All Fields", value: "all" },
        { label: "Customer Name", value: "name" },
        { label: "Phone Number", value: "phone" },
        { label: "Address", value: "address" },
      ],
    },
  ];

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await api.delete(`/customers/${deleteTarget.id}`);
      await fetchCustomers();
    } catch {
      // handled by api.ts
    }
    setDeleteTarget(null);
    setDeleting(false);
  };

  const columns: Column<Customer>[] = [
    {
      header: "Customer Name",
      render: (c) => (
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-secondary text-foreground text-[10px] font-bold shrink-0">
            {c.name.slice(0, 2).toUpperCase()}
          </div>
          <Link href={`/customers/${c.id}/edit`} className="font-medium hover:text-primary transition-colors">
            {c.name}
          </Link>
        </div>
      ),
    },
    {
      header: "Phone Number",
      render: (c) => <span className="text-muted-foreground">{c.phone}</span>,
    },
    {
      header: "Address",
      render: (c) => (
        <span className="inline-flex items-center gap-1 text-muted-foreground max-w-sm truncate">
          <MapPin className="h-3 w-3 text-muted-foreground/70 shrink-0" />
          {c.address || "N/A"}
        </span>
      ),
    },
    {
      header: "Created Date",
      render: (c) => (
        <span className="text-muted-foreground tabular-nums">
          {new Date(c.created_at).toLocaleDateString("en-US", { day: "numeric", month: "short", year: "numeric" })}
        </span>
      ),
    },
    {
      header: "Action",
      align: "right",
      render: (c) => (
        <div className="flex justify-end gap-3">
          <Link
            href={`/customers/${c.id}/edit`}
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
        title="Customers"
        description="Manage your customer directory, phone contacts, and delivery addresses."
        action={
          <Link href="/customers/new">
            <Button size="sm" className="h-8 gap-1.5 text-xs">
              <Plus className="size-3.5" data-icon="inline-start" />
              Add Customer
            </Button>
          </Link>
        }
      />

      <TableToolbar
        searchValue={searchQuery}
        onSearchChange={setSearchQuery}
        searchPlaceholder="Search name, phone, address..."
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
          total={customers.length}
          filteredCount={filtered.length}
          keyExtractor={(c) => c.id}
          emptyMessage="No customers found matching your criteria."
          recordLabel="contacts"
        />
      )}

      <Dialog open={!!deleteTarget} onOpenChange={() => setDeleteTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Customer</DialogTitle>
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
