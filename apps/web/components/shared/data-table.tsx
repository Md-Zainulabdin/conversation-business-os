import { useEffect, useMemo, useState } from "react";
import { cn } from "@/lib/utils";
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";

export interface Column<T> {
  header: string;
  align?: "left" | "right";
  render: (item: T) => React.ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  filteredCount: number;
  keyExtractor: (item: T) => string | number;
  emptyMessage?: string;
  recordLabel?: string;
  pageSize?: number;
}

export function DataTable<T>({
  columns,
  data,
  filteredCount,
  keyExtractor,
  emptyMessage = "No records match your criteria.",
  recordLabel = "records",
  pageSize = 20,
}: DataTableProps<T>) {
  const [page, setPage] = useState(0);
  const pageCount = Math.max(1, Math.ceil(data.length / pageSize));

  useEffect(() => {
    if (page >= pageCount) {
      setPage(Math.max(0, pageCount - 1));
    }
  }, [page, pageCount]);

  const pageData = useMemo(
    () => data.slice(page * pageSize, page * pageSize + pageSize),
    [data, page, pageSize]
  );

  const start = data.length === 0 ? 0 : page * pageSize + 1;
  const end = Math.min(page * pageSize + pageSize, data.length);

  return (
    <div className="rounded-lg border border-border bg-card overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="border-b border-border hover:bg-transparent">
            {columns.map((col, i) => (
              <TableHead
                key={i}
                className={cn(
                  "h-10 text-xs font-medium text-muted-foreground",
                  col.align === "right" && "text-right",
                  col.className
                )}
              >
                {col.header}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.length === 0 ? (
            <TableRow>
              <TableCell
                colSpan={columns.length}
                className="h-32 text-center text-sm text-muted-foreground"
              >
                {emptyMessage}
              </TableCell>
            </TableRow>
          ) : (
            pageData.map((item) => (
              <TableRow
                key={keyExtractor(item)}
                className="border-b border-border/50 hover:bg-muted/30 transition-colors"
              >
                {columns.map((col, i) => (
                  <TableCell
                    key={i}
                    className={cn(
                      "py-3 text-[13px]",
                      col.align === "right"
                        ? "text-right tabular-nums"
                        : "text-foreground",
                      col.className
                    )}
                  >
                    {col.render(item)}
                  </TableCell>
                ))}
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
      <div className="flex items-center justify-between border-t border-border px-4 py-2.5 text-xs text-muted-foreground">
        <span>
          Showing{" "}
          <span className="font-medium text-foreground">
            {data.length === 0 ? 0 : `${start}-${end}`}
          </span>{" "}
          of{" "}
          <span className="font-medium text-foreground">{filteredCount}</span>{" "}
          {recordLabel}
        </span>
        {data.length > pageSize && (
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              className="h-7 px-2.5 text-xs"
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
            >
              Previous
            </Button>
            <span className="tabular-nums">
              Page {page + 1} of {pageCount}
            </span>
            <Button
              variant="outline"
              size="sm"
              className="h-7 px-2.5 text-xs"
              onClick={() =>
                setPage((p) => Math.min(pageCount - 1, p + 1))
              }
              disabled={page >= pageCount - 1}
            >
              Next
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
