"use client";

import { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import { TrendingUp, TrendingDown, Wallet, PackageX } from "lucide-react";

import { api } from "@/lib/api";
import { PageHeader } from "@/components/shared/page-header";
import type { OverviewData } from "@/types";

const PERIOD_OPTIONS = [
  { id: "24h", label: "24 hours" },
  { id: "7d", label: "7 days" },
  { id: "30d", label: "30 days" },
  { id: "12m", label: "12 months" },
];

const PIE_COLORS = [
  "#0f766e",
  "#0284c7",
  "#7c3aed",
  "#d97706",
  "#dc2626",
  "#16a34a",
  "#db2777",
  "#64748b",
];

const tooltipStyle = {
  borderRadius: 8,
  border: "1px solid var(--color-border)",
  fontSize: 12,
};

function formatMoney(value: number): string {
  return `Rs ${value.toLocaleString("en-PK", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

export default function ReportsPage() {
  const [selectedPeriod, setSelectedPeriod] = useState("30d");
  const [data, setData] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get<OverviewData>(`/stats/overview?period=${selectedPeriod}`)
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [selectedPeriod]);

  const kpis = [
    {
      label: "Revenue",
      value: data?.total_sales ?? 0,
      icon: TrendingUp,
      tone: "text-emerald-600",
    },
    {
      label: "Expenses",
      value: data?.expenses_total ?? 0,
      icon: Wallet,
      tone: "text-amber-600",
    },
    {
      label: "Profit",
      value: data?.profit ?? 0,
      icon: data && data.profit < 0 ? TrendingDown : TrendingUp,
      tone: data && data.profit < 0 ? "text-red-600" : "text-teal-600",
    },
    {
      label: "Low Stock",
      value: data?.low_stock_count ?? 0,
      icon: PackageX,
      tone: data && data.low_stock_count > 0 ? "text-red-600" : "text-muted-foreground",
    },
  ];

  return (
    <div className="mx-auto max-w-7xl space-y-5">
      <PageHeader
        title="Reports & Analytics"
        description="Revenue, expenses, profit, and inventory health for the selected period."
        action={
          <div className="flex items-center rounded-lg border border-border bg-card p-0.5">
            {PERIOD_OPTIONS.map((period) => (
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
        }
      />

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {kpis.map((kpi) => (
          <div key={kpi.label} className="rounded-lg border border-border bg-card p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-muted-foreground">
                {kpi.label}
              </span>
              <kpi.icon className={`h-4 w-4 ${kpi.tone}`} />
            </div>
            <p className="mt-2 text-2xl font-semibold tracking-tight text-foreground tabular-nums">
              {loading
                ? "…"
                : kpi.label === "Low Stock"
                  ? kpi.value.toLocaleString("en-US")
                  : formatMoney(kpi.value)}
            </p>
          </div>
        ))}
      </div>

      <div className="grid gap-5 lg:grid-cols-3">
        <div className="rounded-lg border border-border bg-card p-4 lg:col-span-2">
          <h2 className="text-sm font-semibold text-foreground">Revenue trend</h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Daily sales for the selected period
          </p>
          <div className="mt-4 h-64">
            {loading ? (
              <div className="flex h-full items-center justify-center text-xs text-muted-foreground">
                Loading...
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data?.daily_sales ?? []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 11 }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 11 }}
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(value: number) => `Rs ${value}`}
                  />
                  <Tooltip contentStyle={tooltipStyle} formatter={(value) => [formatMoney(Number(value)), "Revenue"]} />
                  <Bar dataKey="amount" fill="#0f766e" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card p-4">
          <h2 className="text-sm font-semibold text-foreground">Expense breakdown</h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Spending by category
          </p>
          <div className="mt-4 h-64">
            {loading ? (
              <div className="flex h-full items-center justify-center text-xs text-muted-foreground">
                Loading...
              </div>
            ) : (data?.expense_breakdown ?? []).length === 0 ? (
              <div className="flex h-full items-center justify-center text-xs text-muted-foreground">
                No expenses in this period
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data?.expense_breakdown ?? []}
                    dataKey="amount"
                    nameKey="category"
                    innerRadius={45}
                    outerRadius={75}
                    paddingAngle={2}
                  >
                    {(data?.expense_breakdown ?? []).map((entry, index) => (
                      <Cell key={entry.category} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={tooltipStyle} formatter={(value) => formatMoney(Number(value))} />
                  <Legend
                    wrapperStyle={{ fontSize: 11 }}
                    formatter={(value: string) => <span className="text-muted-foreground">{value}</span>}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <div className="rounded-lg border border-border bg-card p-4">
          <h2 className="text-sm font-semibold text-foreground">Top products</h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Best sellers by revenue
          </p>
          <div className="mt-4 h-56">
            {loading ? (
              <div className="flex h-full items-center justify-center text-xs text-muted-foreground">
                Loading...
              </div>
            ) : (data?.top_products ?? []).length === 0 ? (
              <div className="flex h-full items-center justify-center text-xs text-muted-foreground">
                No sales in this period
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data?.top_products ?? []} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" horizontal={false} />
                  <XAxis
                    type="number"
                    tick={{ fontSize: 11 }}
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(value: number) => `Rs ${value}`}
                  />
                  <YAxis
                    type="category"
                    dataKey="name"
                    width={110}
                    tick={{ fontSize: 11 }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip contentStyle={tooltipStyle} formatter={(value) => [formatMoney(Number(value)), "Revenue"]} />
                  <Bar dataKey="revenue" fill="#0284c7" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card p-4">
          <h2 className="text-sm font-semibold text-foreground">Top customers</h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Highest spenders in this period
          </p>
          <div className="mt-4 divide-y divide-border">
            {loading ? (
              <p className="py-6 text-center text-xs text-muted-foreground">Loading...</p>
            ) : (data?.top_customers ?? []).length === 0 ? (
              <p className="py-6 text-center text-xs text-muted-foreground">
                No customer sales in this period
              </p>
            ) : (
              (data?.top_customers ?? []).map((customer, index) => (
                <div key={customer.name} className="flex items-center justify-between py-2.5">
                  <div className="flex items-center gap-3 min-w-0">
                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-muted text-[11px] font-medium text-muted-foreground">
                      {index + 1}
                    </span>
                    <span className="truncate text-sm font-medium text-foreground">
                      {customer.name}
                    </span>
                  </div>
                  <span className="text-sm font-semibold text-foreground tabular-nums">
                    {formatMoney(customer.spend)}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card p-4">
        <h2 className="text-sm font-semibold text-foreground">Low stock alerts</h2>
        <p className="text-xs text-muted-foreground mt-0.5">
          Products at or below their minimum stock level
        </p>
        <div className="mt-4 overflow-x-auto">
          {loading ? (
            <p className="py-6 text-center text-xs text-muted-foreground">Loading...</p>
          ) : (data?.low_stock ?? []).length === 0 ? (
            <p className="py-6 text-center text-xs text-muted-foreground">
              All products are above their minimum stock levels
            </p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-[11px] uppercase tracking-wider text-muted-foreground">
                  <th className="pb-2 pr-4 font-medium">Product</th>
                  <th className="pb-2 pr-4 font-medium">SKU</th>
                  <th className="pb-2 pr-4 font-medium">In stock</th>
                  <th className="pb-2 font-medium">Minimum</th>
                </tr>
              </thead>
              <tbody>
                {(data?.low_stock ?? []).map((item) => (
                  <tr key={item.id} className="border-b border-border/60 last:border-0">
                    <td className="py-2.5 pr-4 font-medium text-foreground">{item.name}</td>
                    <td className="py-2.5 pr-4 text-muted-foreground">{item.sku}</td>
                    <td className="py-2.5 pr-4">
                      <span className="inline-flex items-center rounded-full bg-red-50 px-2 py-0.5 text-[11px] font-medium text-red-700 ring-1 ring-inset ring-red-600/20">
                        {item.stock_quantity} {item.unit}
                      </span>
                    </td>
                    <td className="py-2.5 text-muted-foreground">{item.minimum_stock}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}