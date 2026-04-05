import type { ReactNode } from "react";
import { cn } from "../../lib/cn";
import { Badge } from "../ui/Badge";
import { Card } from "../ui/Card";
import { Icon } from "../ui/Icon";

type SearchFilterToolbarProps = {
  title?: string;
  description?: string;
  search?: ReactNode;
  filters?: ReactNode;
  actions?: ReactNode;
  activeFilters?: string[];
  className?: string;
};

export function SearchFilterToolbar({
  title,
  description,
  search,
  filters,
  actions,
  activeFilters,
  className
}: SearchFilterToolbarProps) {
  return (
    <Card tone="subtle" className={cn("p-4", className)}>
      <div className="flex flex-col gap-4">
        {title || description ? (
          <div className="space-y-2">
            {title ? <p className="type-heading-sm">{title}</p> : null}
            {description ? <p className="type-body-sm">{description}</p> : null}
          </div>
        ) : null}
        <div className="flex flex-col gap-3 xl:flex-row xl:items-center">
          <div className="min-w-0 flex-1">{search}</div>
          <div className="flex flex-1 flex-col gap-3 md:flex-row md:flex-wrap">
            {filters}
          </div>
          {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
        </div>
        {activeFilters?.length ? (
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-2 text-body-sm text-content-muted">
              <Icon name="filter" className="h-4 w-4" />
              Active filters
            </span>
            {activeFilters.map((filterValue) => (
              <Badge key={filterValue} tone="outline">
                {filterValue}
              </Badge>
            ))}
          </div>
        ) : null}
      </div>
    </Card>
  );
}
