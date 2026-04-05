import type { ReactNode } from "react";
import { cn } from "../../lib/cn";

export type KeyValueItem = {
  label: string;
  value: ReactNode;
  mono?: boolean;
  emphasized?: boolean;
};

type KeyValueGridProps = {
  items: KeyValueItem[];
  columns?: 2 | 3 | 4;
  className?: string;
};

const columnClasses: Record<NonNullable<KeyValueGridProps["columns"]>, string> = {
  2: "md:grid-cols-2",
  3: "md:grid-cols-2 xl:grid-cols-3",
  4: "md:grid-cols-2 xl:grid-cols-4"
};

export function KeyValueGrid({
  items,
  columns = 3,
  className
}: KeyValueGridProps) {
  return (
    <div className={cn("grid gap-3", columnClasses[columns], className)}>
      {items.map((item) => (
        <div
          key={item.label}
          className="rounded-panel border border-border-subtle bg-surface-subtle/65 p-4"
        >
          <p className="type-label-sm">{item.label}</p>
          <div
            className={cn(
              "mt-2 text-body-sm text-content-secondary",
              item.mono && "type-mono-sm",
              item.emphasized && "font-medium text-content-primary"
            )}
          >
            {item.value}
          </div>
        </div>
      ))}
    </div>
  );
}
