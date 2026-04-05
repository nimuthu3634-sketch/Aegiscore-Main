import { Badge } from "../ui/Badge";

export type TimelineItem = {
  id: string;
  timestamp: string;
  actor: string;
  title: string;
  description: string;
  tone?: "neutral" | "brand" | "warning" | "danger" | "success";
};

type ActivityTimelineProps = {
  items: TimelineItem[];
};

export function ActivityTimeline({ items }: ActivityTimelineProps) {
  return (
    <div className="space-y-4">
      {items.map((item, index) => (
        <div key={item.id} className="relative pl-8">
          {index < items.length - 1 ? (
            <span className="absolute left-[10px] top-6 h-[calc(100%+0.75rem)] w-px bg-border-subtle" />
          ) : null}
          <span className="absolute left-0 top-1 inline-flex h-5 w-5 items-center justify-center rounded-full border border-brand-primary/30 bg-surface-accentSoft" />
          <div className="rounded-panel border border-border-subtle bg-surface-subtle/65 p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-body-sm font-medium text-content-primary">{item.title}</p>
                <p className="mt-1 type-body-sm">{item.description}</p>
              </div>
              <Badge tone={item.tone ?? "outline"}>{item.actor}</Badge>
            </div>
            <p className="mt-3 type-mono-sm">{item.timestamp}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
