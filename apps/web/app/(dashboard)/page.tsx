"use client";

import { useState, useEffect, useMemo } from "react";
import { api } from "@/lib/api";
import { OverviewData, Transaction } from "@/types";
import { TableToolbar, type FilterConfig, type FilterPill } from "@/components/shared/table-toolbar";
import { DataTable, type Column } from "@/components/shared/data-table";
import { useDebounce } from "@/lib/hooks/use-debounce";

export default function DashboardPage() {
  const [selectedPeriod, setSelectedPeriod] = useState("30d");
  const [data, setData] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const debouncedSearch = useDebounce(searchQuery, 200);
  const [selectedTypeFilter, setSelectedTypeFilter] = useState("all");

  useEffect(() => {
    setLoading(true);
    api.get<OverviewData>(`/stats/overview?period=${selectedPeriod}`)
      .then((res) => setData(res))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [selectedPeriod]);

  const periodOptions = [
    { id: "12m", label: "12 months" },
    { id: "30d", label: "30 days" },
    { id: "7d", label: "7 days" },
    { id: "24h", label: "24 hours" },
  ];

  const transactions = data?.transactions ?? [];

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

  const typeStyles: Record<string, string> = {
    Sale: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
    Purchase: "bg-blue-50 text-blue-700 ring-blue-600/20",
    Expense: "bg-amber-50 text-amber-700 ring-amber-600/20",
  };

  const columns: Column<Transaction>[] = [
    {
      header: "Type",
      render: (t) => (
        <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium ring-1 ring-inset ${typeStyles[t.type] ?? "bg-muted text-muted-foreground ring-border"}`}>
          {t.type}
        </span>
      ),
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
          <span className="text-xs font-medium text-muted-foreground">Total Sales</span>
          <p className="mt-2 text-2xl font-semibold tracking-tight text-foreground tabular-nums">
            {loading ? "…" : `Rs ${(data?.total_sales ?? 0).toLocaleString("en-US", { minimumFractionDigits: 2 })}`}
          </p>
        </div>

        <div className="rounded-lg border border-border bg-card p-4">
          <span className="text-xs font-medium text-muted-foreground">Stock Items</span>
          <p className="mt-2 text-2xl font-semibold tracking-tight text-foreground tabular-nums">
            {loading ? "…" : (data?.stock_items ?? 0).toLocaleString("en-US")}
          </p>
        </div>

        <div className="rounded-lg border border-border bg-card p-4">
          <span className="text-xs font-medium text-muted-foreground">Active Customers</span>
          <p className="mt-2 text-2xl font-semibold tracking-tight text-foreground tabular-nums">
            {loading ? "…" : (data?.active_customers ?? 0).toLocaleString("en-US")}
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
        emptyMessage={loading ? "Loading..." : "No transactions match your query."}
        recordLabel="transactions"
      />
    </div>
  );
}
