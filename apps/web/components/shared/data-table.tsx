import { cn } from "@/lib/utils";
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from "@/components/ui/table";

export interface Column<T> {
  header: string;
  align?: "left" | "right";
  render: (item: T) => React.ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  total: number;
  filteredCount: number;
  keyExtractor: (item: T) => string | number;
  emptyMessage?: string;
  recordLabel?: string;
}

export function DataTable<T>({
  columns,
  data,
  total,
  filteredCount,
  keyExtractor,
  emptyMessage = "No records match your criteria.",
  recordLabel = "records",
}: DataTableProps<T>) {
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
            data.map((item) => (
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
          <span className="font-medium text-foreground">{filteredCount}</span>{" "}
          of{" "}
          <span className="font-medium text-foreground">{total}</span>{" "}
          {recordLabel}
        </span>
      </div>
    </div>
  );
}
