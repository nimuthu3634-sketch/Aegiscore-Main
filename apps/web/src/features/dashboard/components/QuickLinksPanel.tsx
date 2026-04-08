import type { IconName } from "../../../lib/theme/tokens";
import { Button } from "../../../components/ui/Button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "../../../components/ui/Card";
import { Icon } from "../../../components/ui/Icon";

type QuickLinkItem = {
  id: string;
  label: string;
  description: string;
  value: string;
  icon: IconName;
  onClick: () => void;
};

type QuickLinksPanelProps = {
  items: QuickLinkItem[];
};

export function QuickLinksPanel({ items }: QuickLinksPanelProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <div className="space-y-2">
          <p className="type-label-md">Analyst workflow</p>
          <CardTitle>Next steps</CardTitle>
          <CardDescription>
            Numbers shown are live summary counts—use them to jump straight into triage,
            incidents, assets, or response audit.
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 pt-0">
        {items.map((item) => (
          <Button
            key={item.id}
            variant="secondary"
            className="h-auto w-full justify-between rounded-panel px-4 py-3"
            onClick={item.onClick}
          >
            <span className="flex min-w-0 items-start gap-3 text-left">
              <span className="mt-0.5 inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-panel border border-border-subtle bg-surface-subtle/60 text-brand-primary">
                <Icon name={item.icon} className="h-4 w-4" />
              </span>
              <span className="min-w-0">
                <span className="block text-body-sm font-semibold text-content-primary">
                  {item.label}
                </span>
                <span className="block type-body-sm">{item.description}</span>
              </span>
            </span>
            <span className="type-mono-sm">{item.value}</span>
          </Button>
        ))}
      </CardContent>
    </Card>
  );
}
