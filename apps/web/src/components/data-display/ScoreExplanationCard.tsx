import type { ReactNode } from "react";
import { Badge } from "../ui/Badge";
import { EvidencePanel } from "./EvidencePanel";

type ScoreExplanationCardProps = {
  label: string;
  summary: string;
  rationale: string;
  scoreValue?: ReactNode;
  factors: string[];
};

export function ScoreExplanationCard({
  label,
  summary,
  rationale,
  scoreValue,
  factors
}: ScoreExplanationCardProps) {
  return (
    <EvidencePanel
      eyebrow="Scoring"
      title={label}
      description={summary}
      actions={scoreValue ? <Badge tone="brand">{scoreValue}</Badge> : null}
    >
      <div className="space-y-4">
        <p className="type-body-sm">{rationale}</p>
        <div className="space-y-2">
          <p className="type-label-sm">Key factors</p>
          <ul className="space-y-2">
            {factors.map((factor) => (
              <li
                key={factor}
                className="rounded-panel border border-border-subtle bg-surface-subtle/65 px-4 py-3 text-body-sm text-content-secondary"
              >
                {factor}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </EvidencePanel>
  );
}
