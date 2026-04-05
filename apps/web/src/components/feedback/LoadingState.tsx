import { cn } from "../../lib/cn";
import { Card, CardContent, CardHeader } from "../ui/Card";

type SkeletonProps = {
  className?: string;
};

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-gradient-to-r from-surface-subtle via-surface-raised to-surface-subtle",
        className
      )}
      aria-hidden="true"
    />
  );
}

type LoadingCardProps = {
  className?: string;
};

export function LoadingCard({ className }: LoadingCardProps) {
  return (
    <Card className={cn("h-full", className)}>
      <CardHeader className="flex-col items-start gap-4">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-10 w-28" />
      </CardHeader>
      <CardContent className="space-y-3 pt-0">
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-4/5" />
      </CardContent>
    </Card>
  );
}

type LoadingTableProps = {
  rows?: number;
  columns?: number;
};

export function LoadingTable({
  rows = 4,
  columns = 5
}: LoadingTableProps) {
  return (
    <Card className="overflow-hidden">
      <div className="space-y-4 p-panel">
        <div className="grid gap-3" style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}>
          {Array.from({ length: columns }).map((_, index) => (
            <Skeleton key={`head-${index}`} className="h-3 w-full" />
          ))}
        </div>
        <div className="space-y-3">
          {Array.from({ length: rows }).map((_, rowIndex) => (
            <div
              key={`row-${rowIndex}`}
              className="grid gap-3"
              style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}
            >
              {Array.from({ length: columns }).map((_, columnIndex) => (
                <Skeleton
                  key={`cell-${rowIndex}-${columnIndex}`}
                  className="h-4 w-full"
                />
              ))}
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}
