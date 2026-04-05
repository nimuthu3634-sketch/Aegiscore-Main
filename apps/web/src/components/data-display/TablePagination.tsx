import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";

type TablePaginationProps = {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
  itemLabel: string;
  onPageChange: (page: number) => void;
};

export function TablePagination({
  page,
  pageSize,
  total,
  totalPages,
  itemLabel,
  onPageChange
}: TablePaginationProps) {
  const start = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const end = total === 0 ? 0 : Math.min(page * pageSize, total);

  return (
    <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
      <p className="type-body-sm">
        Showing <span className="text-content-primary">{start}</span>-
        <span className="text-content-primary">{end}</span> of{" "}
        <span className="text-content-primary">{total}</span> {itemLabel}
      </p>
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          Previous
        </Button>
        <Badge tone="outline">
          Page {page} / {Math.max(totalPages, 1)}
        </Badge>
        <Button
          variant="ghost"
          size="sm"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
        >
          Next
        </Button>
      </div>
    </div>
  );
}
