"use client";

import { Search, Filter, X, ChevronDown } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export interface FilterConfig {
  value: string;
  onChange: (value: string) => void;
  options: { label: string; value: string }[];
}

export interface FilterPill {
  label: string;
  onRemove: () => void;
}

interface TableToolbarProps {
  searchValue: string;
  onSearchChange: (value: string) => void;
  searchPlaceholder?: string;
  filters?: FilterConfig[];
  filterPills?: FilterPill[];
  onClearFilters?: () => void;
}

export function TableToolbar({
  searchValue,
  onSearchChange,
  searchPlaceholder = "Search",
  filters = [],
  filterPills = [],
  onClearFilters,
}: TableToolbarProps) {
  const hasActiveFilters = filterPills.length > 0;

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-2">
        <div className="relative">
          <Search className="absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground pointer-events-none" />
          <Input
            type="search"
            placeholder={searchPlaceholder}
            value={searchValue}
            onChange={(e) => onSearchChange(e.target.value)}
            className="h-7 w-48 pl-7 border-border bg-card"
          />
        </div>
        {filters.map((filter, i) => (
          <div key={i} className="relative">
            <select
              value={filter.value}
              onChange={(e) => filter.onChange(e.target.value)}
              className="h-7 appearance-none rounded-md border border-border bg-card pl-2 pr-6 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring cursor-pointer"
            >
              {filter.options.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <ChevronDown className="pointer-events-none absolute right-1.5 top-1/2 h-3 w-3 -translate-y-1/2 text-muted-foreground" />
          </div>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Button
          variant={hasActiveFilters ? "default" : "outline"}
          size="sm"
          onClick={onClearFilters}
          className="h-7 gap-1.5 px-2.5 text-xs font-medium"
        >
          <Filter className="h-3 w-3" />
          Filters
          {hasActiveFilters && (
            <span className="flex h-4 w-4 items-center justify-center rounded-full bg-primary-foreground/20 text-[10px] font-bold">
              {filterPills.length}
            </span>
          )}
        </Button>
        {filterPills.map((pill, i) => (
          <span
            key={i}
            className="inline-flex items-center gap-1 rounded-md border border-border bg-card px-2 py-0.5 text-[11px] text-foreground"
          >
            {pill.label}
            <button
              type="button"
              onClick={pill.onRemove}
              className="ml-0.5 text-muted-foreground hover:text-foreground"
            >
              <X className="h-3 w-3" />
            </button>
          </span>
        ))}
        {hasActiveFilters && onClearFilters && (
          <button
            type="button"
            onClick={onClearFilters}
            className="text-xs font-medium text-primary hover:underline"
          >
            Clear filters
          </button>
        )}
      </div>
    </div>
  );
}
