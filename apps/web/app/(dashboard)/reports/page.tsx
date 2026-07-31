"use client";

import { useState, useMemo } from "react";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import initialData from "@/lib/data/dummy.json";
import { Report } from "@/types";
import { PageHeader } from "@/components/shared/page-header";
import { TableToolbar, type FilterConfig, type FilterPill } from "@/components/shared/table-toolbar";
import { DataTable, type Column } from "@/components/shared/data-table";
import { useDebounce } from "@/lib/hooks/use-debounce";

export default function ReportsPage() {
  const [reports] = useState<Report[]>(initialData.reports);
  const [searchQuery, setSearchQuery] = useState("");
  const debouncedSearch = useDebounce(searchQuery, 200);
  const [selectedCategoryFilter, setSelectedCategoryFilter] = useState("all");
  const reportCategories = ["Daily Summary", "Low Stock Alert", "Inventory Health", "Revenue Audit"];

  const filteredReports = useMemo(
    () => reports.filter((rep) => {
      const query = debouncedSearch.toLowerCase();
      const matchesSearch =
        !query ||
        rep.title.toLowerCase().includes(query) ||
        rep.category.toLowerCase().includes(query) ||
        (rep.notes || "").toLowerCase().includes(query) ||
        rep.report_date.includes(query);

      const matchesCategory =
        selectedCategoryFilter === "all" || rep.category === selectedCategoryFilter;

      return matchesSearch && matchesCategory;
    }),
    [reports, debouncedSearch, selectedCategoryFilter]
  );

  const clearFilters = () => {
    setSelectedCategoryFilter("all");
    setSearchQuery("");
  };

  const filterPills: FilterPill[] = [];
  if (selectedCategoryFilter !== "all") {
    filterPills.push({ label: `Category: ${selectedCategoryFilter}`, onRemove: () => setSelectedCategoryFilter("all") });
  }

  const filters: FilterConfig[] = [
    {
      value: selectedCategoryFilter,
      onChange: setSelectedCategoryFilter,
      options: [
        { label: "All Categories", value: "all" },
        ...reportCategories.map((cat) => ({ label: cat, value: cat })),
      ],
    },
  ];

  const columns: Column<Report>[] = [
    {
      header: "Date",
      render: (r) => <span className="text-muted-foreground tabular-nums">{r.report_date}</span>,
    },
    { header: "Report Title", render: (r) => <span className="font-medium">{r.title}</span> },
    { header: "Category", render: (r) => r.category },
    { header: "Sales", align: "right", render: (r) => r.total_sales_count },
    { header: "Revenue", align: "right", render: (r) => <span>Rs {r.total_revenue.toFixed(2)}</span> },
    { header: "Expenses", align: "right", render: (r) => <span className="text-muted-foreground">Rs {r.total_expenses.toFixed(2)}</span> },
    { header: "Net Profit", align: "right", render: (r) => <span className="font-medium">Rs {r.net_profit.toFixed(2)}</span> },
    {
      header: "Remarks",
      render: (r) => <span className="text-muted-foreground max-w-[200px] truncate block">{r.notes || "—"}</span>,
    },
  ];

  return (
    <div className="mx-auto max-w-7xl space-y-5">
      <PageHeader
        title="Reports & Analytics"
        description="Daily sales summaries, gross revenue metrics, and inventory health audits."
        action={
          <Button size="sm" className="gap-1.5 self-start sm:self-auto text-xs font-medium">
            <Plus className="h-3.5 w-3.5" />
            Generate Report
          </Button>
        }
      />

      <TableToolbar
        searchValue={searchQuery}
        onSearchChange={setSearchQuery}
        filters={filters}
        filterPills={filterPills}
        onClearFilters={clearFilters}
      />

      <DataTable
        columns={columns}
        data={filteredReports}
        total={reports.length}
        filteredCount={filteredReports.length}
        keyExtractor={(r) => r.id}
        emptyMessage="No reports match your criteria."
        recordLabel="reports"
      />
    </div>
  );
}
