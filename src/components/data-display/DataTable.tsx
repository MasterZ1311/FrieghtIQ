"use client";

import React, { useState } from "react";
import { ChevronDown, ChevronUp, ChevronsUpDown, Search, ChevronLeft, ChevronRight } from "lucide-react";
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export interface ColumnDef<T> {
  header: string;
  accessorKey?: keyof T | string;
  cell?: (row: T) => React.ReactNode;
  sortable?: boolean;
  className?: string;
}

interface DataTableProps<T> {
  data: T[];
  columns: ColumnDef<T>[];
  searchPlaceholder?: string;
  searchKey?: keyof T;
  pageSize?: number;
  emptyMessage?: string;
  className?: string;
  title?: string;
  headerAction?: React.ReactNode;
}

export function DataTable<T extends Record<string, any>>({
  data,
  columns,
  searchPlaceholder = "Search records...",
  searchKey,
  pageSize = 5,
  emptyMessage = "No matching records found",
  className = "",
  title,
  headerAction,
}: DataTableProps<T>) {
  const [searchTerm, setSearchTerm] = useState("");
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortAsc, setSortAsc] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);

  // Filter
  const filteredData = data.filter((item) => {
    if (!searchTerm) return true;
    if (searchKey) {
      const val = item[searchKey];
      return val ? String(val).toLowerCase().includes(searchTerm.toLowerCase()) : false;
    }
    // General search across all values
    return Object.values(item).some((val) =>
      val ? String(val).toLowerCase().includes(searchTerm.toLowerCase()) : false
    );
  });

  // Sort
  const sortedData = [...filteredData].sort((a, b) => {
    if (!sortKey) return 0;
    const valA = a[sortKey];
    const valB = b[sortKey];
    if (valA === valB) return 0;
    if (valA === null || valA === undefined) return 1;
    if (valB === null || valB === undefined) return -1;
    if (valA < valB) return sortAsc ? -1 : 1;
    return sortAsc ? 1 : -1;
  });

  // Pagination
  const totalPages = Math.ceil(sortedData.length / pageSize) || 1;
  const paginatedData = sortedData.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  const handleSort = (key: string) => {
    if (sortKey === key) {
      if (sortAsc) {
        setSortAsc(false);
      } else {
        setSortKey(null);
        setSortAsc(true);
      }
    } else {
      setSortKey(key);
      setSortAsc(true);
    }
  };

  return (
    <div className={`rounded-xl border border-border bg-card overflow-hidden ${className}`}>
      {/* Table Header Bar */}
      {(title || searchPlaceholder || headerAction) && (
        <div className="p-4 border-b border-border flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-muted/20">
          {title && (
            <h4 className="text-sm sm:text-base font-bold text-foreground tracking-tight">
              {title}
            </h4>
          )}

          <div className="flex items-center gap-3 ml-auto w-full sm:w-auto">
            <div className="relative flex-1 sm:w-64">
              <Search className="absolute left-2.5 top-2 h-3.5 w-3.5 text-muted-foreground pointer-events-none" />
              <Input
                type="text"
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setCurrentPage(1);
                }}
                placeholder={searchPlaceholder}
                className="h-8 pl-8 pr-3 text-xs bg-background/80"
              />
            </div>
            {headerAction}
          </div>
        </div>
      )}

      {/* Table Content */}
      <div className="overflow-x-auto">
        <Table>
          <TableHeader className="bg-muted/40 font-mono text-[11px] uppercase tracking-wider">
            <TableRow className="border-border hover:bg-transparent">
              {columns.map((col, idx) => (
                <TableHead
                  key={idx}
                  className={`py-3 px-4 font-semibold text-muted-foreground ${col.className || ""}`}
                  onClick={() => {
                    if (col.sortable && col.accessorKey) {
                      handleSort(String(col.accessorKey));
                    }
                  }}
                >
                  <div className={`flex items-center gap-1.5 ${col.sortable ? "cursor-pointer select-none hover:text-foreground" : ""}`}>
                    <span>{col.header}</span>
                    {col.sortable && col.accessorKey && (
                      <span className="text-muted-foreground">
                        {sortKey === col.accessorKey ? (
                          sortAsc ? (
                            <ChevronUp className="h-3.5 w-3.5 text-primary" />
                          ) : (
                            <ChevronDown className="h-3.5 w-3.5 text-primary" />
                          )
                        ) : (
                          <ChevronsUpDown className="h-3 w-3 opacity-50" />
                        )}
                      </span>
                    )}
                  </div>
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody className="font-sans text-xs">
            {paginatedData.length > 0 ? (
              paginatedData.map((row, rowIdx) => (
                <TableRow
                  key={rowIdx}
                  className="border-border hover:bg-muted/40 transition-colors"
                >
                  {columns.map((col, colIdx) => (
                    <TableCell
                      key={colIdx}
                      className={`py-3 px-4 ${col.className || ""}`}
                    >
                      {col.cell
                        ? col.cell(row)
                        : col.accessorKey
                        ? String(row[col.accessorKey as string] ?? "—")
                        : "—"}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="py-8 text-center text-xs text-muted-foreground"
                >
                  {emptyMessage}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination Footer */}
      <div className="px-4 py-3 border-t border-border flex items-center justify-between gap-2 text-xs text-muted-foreground bg-muted/10">
        <div>
          Showing{" "}
          <span className="font-semibold text-foreground font-mono">
            {filteredData.length > 0 ? (currentPage - 1) * pageSize + 1 : 0}
          </span>{" "}
          to{" "}
          <span className="font-semibold text-foreground font-mono">
            {Math.min(currentPage * pageSize, filteredData.length)}
          </span>{" "}
          of{" "}
          <span className="font-semibold text-foreground font-mono">
            {filteredData.length}
          </span>{" "}
          results
        </div>

        <div className="flex items-center gap-1.5">
          <Button
            variant="outline"
            size="icon-sm"
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="h-7 w-7"
            aria-label="Previous page"
          >
            <ChevronLeft className="h-3.5 w-3.5" />
          </Button>

          <span className="px-2 text-xs font-mono text-foreground">
            {currentPage} / {totalPages}
          </span>

          <Button
            variant="outline"
            size="icon-sm"
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            className="h-7 w-7"
            aria-label="Next page"
          >
            <ChevronRight className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>
    </div>
  );
}
