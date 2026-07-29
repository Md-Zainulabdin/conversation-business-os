"use client";

import { Package, Tags, AlertTriangle, Activity } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const stats = [
  { label: "Total Products", value: "—", icon: Package },
  { label: "Categories", value: "—", icon: Tags },
  { label: "Low Stock", value: "—", icon: AlertTriangle },
  { label: "Active", value: "—", icon: Activity },
];

export default function DashboardPage() {
  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-8">
        <h1 className="text-lg font-semibold tracking-tight text-foreground">Dashboard</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">Welcome back</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.label}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  {stat.label}
                </CardTitle>
                <Icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-semibold tracking-tight text-foreground">{stat.value}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
