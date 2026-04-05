import { Card } from "../ui/Card";

type QueryWarningsProps = {
  warnings: string[];
};

export function QueryWarnings({ warnings }: QueryWarningsProps) {
  if (!warnings.length) {
    return null;
  }

  return (
    <Card tone="subtle" className="border border-status-warning/25 px-4 py-3">
      <div className="space-y-1">
        <p className="type-label-sm text-status-warning">Server query notes</p>
        {warnings.map((warning) => (
          <p key={warning} className="type-body-sm text-content-secondary">
            {warning}
          </p>
        ))}
      </div>
    </Card>
  );
}
