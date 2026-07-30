"use client";

import { useState, useMemo } from "react";
import { ArrowUpRight, Calendar } from "lucide-react";
import initialData from "@/lib/data/dummy.json";
import { Transaction } from "@/types";
import { TableToolbar, type FilterConfig, type FilterPill } from "@/components/shared/table-toolbar";
import { DataTable, type Column } from "@/components/shared/data-table";
import { useDebounce } from "@/lib/hooks/use-debounce";

export default function DashboardPage() {
  const [selectedPeriod, setSelectedPeriod] = useState("30d");
  const [transactions] = useState<Transaction[]>(initialData?.overview as Transaction[]);
  const [searchQuery, setSearchQuery] = useState("");
  const debouncedSearch = useDebounce(searchQuery, 200);
  const [selectedTypeFilter, setSelectedTypeFilter] = useState("all");

  const periodOptions = [
    { id: "12m", label: "12 months" },
    { id: "30d", label: "30 days" },
    { id: "7d", label: "7 days" },
    { id: "24h", label: "24 hours" },
  ];

  const filteredTransactions = useMemo(
    () => transactions.filter((txn) => {
      const query = debouncedSearch.toLowerCase();
      const matchesSearch =
        !query ||
        txn.reference.toLowerCase().includes(query) ||
        txn.entity.toLowerCase().includes(query) ||
        txn.type.toLowerCase().includes(query);

      const matchesType = selectedTypeFilter === "all" || txn.type === selectedTypeFilter;

      return matchesSearch && matchesType;
    }),
    [transactions, debouncedSearch, selectedTypeFilter]
  );

  const clearFilters = () => {
    setSelectedTypeFilter("all");
    setSearchQuery("");
  };

  const filterPills: FilterPill[] = [];
  if (selectedTypeFilter !== "all") {
    filterPills.push({ label: `Type: ${selectedTypeFilter}`, onRemove: () => setSelectedTypeFilter("all") });
  }

  const filters: FilterConfig[] = [
    {
      value: selectedTypeFilter,
      onChange: setSelectedTypeFilter,
      options: [
        { label: "All Types", value: "all" },
        { label: "Sales", value: "Sale" },
        { label: "Purchases", value: "Purchase" },
        { label: "Expenses", value: "Expense" },
      ],
    },
  ];

  const columns: Column<Transaction>[] = [
    {
      header: "Type",
      render: (t) => {
        const styles: Record<string, string> = {
          Sale: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
          Purchase: "bg-blue-50 text-blue-700 ring-blue-600/20",
          Expense: "bg-amber-50 text-amber-700 ring-amber-600/20",
        };
        return (
          <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium ring-1 ring-inset ${styles[t.type]}`}>
            {t.type}
          </span>
        );
      },
    },
    { header: "Reference", render: (t) => <span className="font-medium">{t.reference}</span> },
    { header: "Entity", render: (t) => <span className="text-muted-foreground">{t.entity}</span> },
    { header: "Amount", align: "right", render: (t) => <span className="font-medium">Rs {t.amount.toFixed(2)}</span> },
    { header: "Status", render: (t) => <span className="text-muted-foreground">{t.status}</span> },
    {
      header: "Date",
      render: (t) => (
        <span className="text-muted-foreground tabular-nums">
          {new Date(t.date).toLocaleDateString("en-US", { day: "numeric", month: "short" })}
        </span>
      ),
    },
  ];

  return (
    <div className="mx-auto max-w-7xl space-y-5">
      <div>
        <h1 className="text-lg font-semibold tracking-tight text-foreground">
          My dashboard
        </h1>
        <p className="text-[13px] text-muted-foreground mt-0.5">
          Here&apos;s an overview of your store traffic, inventory, and sales.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground">Total Sales</span>
            <span className="inline-flex items-center rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-700 ring-1 ring-inset ring-emerald-600/20">
              <ArrowUpRight className="mr-0.5 h-3 w-3" />15%
            </span>
          </div>
          <p className="mt-2 text-2xl font-semibold tracking-tight text-foreground tabular-nums">
            Rs 88,820.44
          </p>
        </div>

        <div className="rounded-lg border border-border bg-card p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground">Stock Items</span>
            <span className="inline-flex items-center rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-700 ring-1 ring-inset ring-emerald-600/20">
              <ArrowUpRight className="mr-0.5 h-3 w-3" />6%
            </span>
          </div>
          <p className="mt-2 text-2xl font-semibold tracking-tight text-foreground tabular-nums">
            112,440
          </p>
        </div>

        <div className="rounded-lg border border-border bg-card p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground">Active Customers</span>
            <span className="inline-flex items-center rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-700 ring-1 ring-inset ring-emerald-600/20">
              <ArrowUpRight className="mr-0.5 h-3 w-3" />1%
            </span>
          </div>
          <p className="mt-2 text-2xl font-semibold tracking-tight text-foreground tabular-nums">
            96
          </p>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center rounded-lg border border-border bg-card p-0.5">
          {periodOptions.map((period) => (
            <button
              key={period.id}
              type="button"
              onClick={() => setSelectedPeriod(period.id)}
              className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                selectedPeriod === period.id
                  ? "bg-muted text-foreground font-semibold"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {period.label}
            </button>
          ))}
        </div>

        <button
          type="button"
          className="flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
        >
          <Calendar className="h-3.5 w-3.5" />
          <span>1 Jan 2026 – 31 Dec 2026</span>
        </button>
      </div>

      <TableToolbar
        searchValue={searchQuery}
        onSearchChange={setSearchQuery}
        filters={filters}
        filterPills={filterPills}
        onClearFilters={clearFilters}
      />

      <DataTable
        columns={columns}
        data={filteredTransactions}
        total={transactions.length}
        filteredCount={filteredTransactions.length}
        keyExtractor={(t) => t.id}
        emptyMessage="No transactions match your query."
        recordLabel="transactions"
      />
    </div>
  );
}
