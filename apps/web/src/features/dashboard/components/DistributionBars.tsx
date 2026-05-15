/*
 * Distribution Bars reusable UI component used by the React dashboard.
 */
import { cn } from "../../../lib/cn";
import type { DashboardDistributionPoint } from "../types";

// Defines the Distribution Bars Props data shape used by this frontend module.
type DistributionBarsProps = {
  title: string;
  items: DashboardDistributionPoint[];
  className?: string;
};

// Formats label for display in the dashboard.
function formatLabel(label: string) {
  return label.replace(/_/g, " ");
}

// Renders the Distribution Bars UI section.
export function DistributionBars({
  title,
  items,
  className
}: DistributionBarsProps) {
  const max = Math.max(...items.map((item) => item.total), 1);

  return (
    <div
      className={cn(
        "rounded-panel border border-border-subtle bg-surface-subtle/55 p-4",
        className
      )}
    >
      <p className="type-label-sm">{title}</p>
      <div className="mt-4 space-y-4">
        {items.map((item) => {
          const width = item.total > 0 ? Math.max((item.total / max) * 100, 8) : 0;

          return (
            <div key={item.label} className="space-y-2">
              <div className="flex items-center justify-between gap-3">
                <span className="type-body-sm capitalize">{formatLabel(item.label)}</span>
                <span className="type-mono-sm">{item.total}</span>
              </div>
              <div className="h-2 rounded-full bg-surface-base/80">
                <div
                  className="h-full rounded-full transition-[width] duration-300"
                  style={{
                    width: `${width}%`,
                    backgroundColor: item.color
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
