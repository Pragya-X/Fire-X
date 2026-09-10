"use client";

import { ChevronLeft, ChevronRight, ChevronsUpDown } from "lucide-react";
import { Button } from "@/components/ui/primitives";
import { cn } from "@/lib/utils";

export interface Column<T> {
  key: string;
  header: string;
  render: (row: T) => React.ReactNode;
  sortable?: boolean;
  className?: string;
  hideOnMobile?: boolean;
}

export function DataTable<T>({
  columns,
  rows,
  total,
  page,
  pageSize,
  onPageChange,
  onSort,
  sortKey,
  sortOrder,
  loading,
  onRowClick,
}: {
  columns: Column<T>[];
  rows: T[];
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (p: number) => void;
  onSort?: (key: string) => void;
  sortKey?: string;
  sortOrder?: string;
  loading?: boolean;
  onRowClick?: (row: T) => void;
}) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  return (
    <div className="w-full">
      <div className="overflow-x-auto rounded-lg border border-base-border/70">
        <table className="w-full min-w-[760px] text-left text-xs">
          <thead className="border-b border-base-border/70 bg-base-raised/60">
            <tr>
              {columns.map((c) => (
                <th key={c.key} className={cn("px-3 py-2.5 font-medium text-muted", c.className, c.hideOnMobile && "hidden lg:table-cell")}>
                  <button
                    className={cn("inline-flex items-center gap-1 hover:text-primary", c.sortable && "cursor-pointer")}
                    onClick={() => c.sortable && onSort?.(c.key)}
                    disabled={!c.sortable}
                  >
                    {c.header}
                    {c.sortable && (
                      <ChevronsUpDown className={cn("h-3 w-3", sortKey === c.key && "text-accent")} />
                    )}
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: Math.min(8, pageSize) }).map((_, i) => (
                <tr key={i} className="border-b border-base-border/40">
                  {columns.map((c) => (
                    <td key={c.key} className={cn("px-3 py-3", c.hideOnMobile && "hidden lg:table-cell")}>
                      <div className="h-3 w-20 animate-pulse rounded bg-slate-200/70" />
                    </td>
                  ))}
                </tr>
              ))
            ) : rows.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-3 py-10 text-center text-muted">
                  No records match the current filters.
                </td>
              </tr>
            ) : (
              rows.map((row, i) => (
                <tr
                  key={i}
                  onClick={() => onRowClick?.(row)}
                  className={cn(
                    "border-b border-base-border/40 transition-colors hover:bg-base-panel",
                    onRowClick && "cursor-pointer"
                  )}
                >
                  {columns.map((c) => (
                    <td key={c.key} className={cn("px-3 py-2.5", c.className, c.hideOnMobile && "hidden lg:table-cell")}>
                      {c.render(row)}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <div className="mt-3 flex items-center justify-between text-xs text-muted">
        <span>
          {total.toLocaleString()} records · page {page} / {pages}
        </span>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="icon" disabled={page <= 1} onClick={() => onPageChange(page - 1)} aria-label="Previous page">
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" disabled={page >= pages} onClick={() => onPageChange(page + 1)} aria-label="Next page">
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}