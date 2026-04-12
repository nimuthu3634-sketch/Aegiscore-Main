import type { ReactNode } from "react";
import { EvidencePanel } from "./EvidencePanel";

type ScoreMetadataItem = {
  label: string;
  value: string;
  mono?: boolean;
};

type ScoreExplanationCardProps = {
  label: string;
  summary: string;
  rationale: string;
  scoreValue?: ReactNode;
  factors: string[];
  metadata?: ScoreMetadataItem[];
  drivers?: string[];
  /** Persisted one-line reasoning when distinct from rationale copy. */
  reasoning?: string | null;
  /** Formatted softmax line (e.g. "Low 12% · Medium 27% · High 61%"). */
  classProbabilitiesSummary?: string | null;
};

export function ScoreExplanationCard({
  label,
  summary,
  rationale,
  scoreValue,
  factors,
  metadata,
  drivers,
  reasoning,
  classProbabilitiesSummary
}: ScoreExplanationCardProps) {
  const showReasoning =
    reasoning &&
    reasoning.trim() &&
    reasoning.trim() !== rationale.trim();

  return (
    <EvidencePanel
      eyebrow="Scoring"
      title={label}
      description={summary}
      actions={scoreValue}
    >
      <div className="space-y-4">
        <p className="type-body-sm">{rationale}</p>
        {showReasoning ? (
          <div className="rounded-panel border border-border-subtle bg-surface-base/40 px-4 py-3">
            <p className="type-label-sm">Reasoning</p>
            <p className="type-body-sm mt-2 text-content-secondary">{reasoning}</p>
          </div>
        ) : null}
        {classProbabilitiesSummary ? (
          <div className="rounded-panel border border-brand-primary/25 bg-surface-accentSoft/35 px-4 py-3">
            <p className="type-label-sm">Model class probabilities</p>
            <p className="type-mono-sm mt-2 text-content-primary">{classProbabilitiesSummary}</p>
          </div>
        ) : null}
        {metadata?.length ? (
          <div className="grid gap-3 sm:grid-cols-2">
            {metadata.map((item) => (
              <div
                key={`${item.label}-${item.value}`}
                className="rounded-panel border border-border-subtle bg-surface-subtle/65 px-4 py-3"
              >
                <p className="type-label-sm">{item.label}</p>
                <p className={item.mono ? "type-mono-sm mt-2" : "type-body-sm mt-2"}>
                  {item.value}
                </p>
              </div>
            ))}
          </div>
        ) : null}
        {drivers?.length ? (
          <div className="space-y-2">
            <p className="type-label-sm">Top drivers</p>
            <ul className="space-y-2">
              {drivers.map((driver) => (
                <li
                  key={driver}
                  className="rounded-panel border border-brand-primary/20 bg-surface-accentSoft/40 px-4 py-3 text-body-sm text-content-secondary"
                >
                  {driver}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
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
