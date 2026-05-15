/*
 * Query Warnings reusable UI component used by the React dashboard.
 */
import { Card } from "../ui/Card";

// Defines the Query Warnings Props data shape used by this frontend module.
type QueryWarningsProps = {
  warnings: string[];
};

// Renders the Query Warnings UI section.
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
