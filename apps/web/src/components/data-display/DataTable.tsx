import type { ReactNode } from "react";
import { cn } from "../../lib/cn";
import { Card } from "../ui/Card";

export type TableColumn<T> = {
  id: string;
  header: ReactNode;
  cell: (row: T) => ReactNode;
  align?: "left" | "right";
  headerClassName?: string;
  cellClassName?: string;
};

type DataTableProps<T> = {
  ariaLabel: string;
  columns: TableColumn<T>[];
  data: T[];
  rowKey: (row: T) => string;
  dense?: boolean;
  onRowClick?: (row: T) => void;
  selectedRowKey?: string;
  emptyState?: ReactNode;
  footer?: ReactNode;
  className?: string;
};

export function DataTable<T>({
  ariaLabel,
  columns,
  data,
  rowKey,
  dense = false,
  onRowClick,
  selectedRowKey,
  emptyState,
  footer,
  className
}: DataTableProps<T>) {
  const cellPadding = dense ? "px-4 py-3" : "px-4 py-4";

  return (
    <Card className={cn("overflow-hidden", className)}>
      <div className="overflow-x-auto">
        <table aria-label={ariaLabel} className="min-w-full border-collapse">
          <thead className="bg-surface-panel/80">
            <tr>
              {columns.map((column) => (
                <th
                  key={column.id}
                  className={cn(
                    cellPadding,
                    "type-label-sm border-b border-border-subtle text-left align-middle",
                    column.align === "right" && "text-right",
                    column.headerClassName
                  )}
                  scope="col"
                >
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.length ? (
              data.map((row) => {
                const key = rowKey(row);
                const isSelected = selectedRowKey === key;

                return (
                  <tr
                    key={key}
                    className={cn(
                      "border-b border-border-subtle transition last:border-b-0",
                      onRowClick && "cursor-pointer hover:bg-surface-accentSoft/40",
                      isSelected &&
                        "bg-surface-accentSoft/60 shadow-[inset_2px_0_0_0_rgba(249,115,22,1)]"
                    )}
                    onClick={onRowClick ? () => onRowClick(row) : undefined}
                  >
                    {columns.map((column) => (
                      <td
                        key={column.id}
                        className={cn(
                          cellPadding,
                          "align-middle text-body-sm text-content-secondary",
                          column.align === "right" && "text-right",
                          column.cellClassName
                        )}
                      >
                        {column.cell(row)}
                      </td>
                    ))}
                  </tr>
                );
              })
            ) : (
              <tr>
                <td
                  className="px-4 py-10 text-center text-body-sm text-content-muted"
                  colSpan={columns.length}
                >
                  {emptyState ?? "No data available."}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {footer ? <div className="border-t border-border-subtle px-4 py-3">{footer}</div> : null}
    </Card>
  );
}
