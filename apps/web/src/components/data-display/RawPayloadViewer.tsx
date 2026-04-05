import { useState } from "react";
import { Button } from "../ui/Button";
import { EvidencePanel } from "./EvidencePanel";

type RawPayloadViewerProps = {
  payload: unknown;
  title?: string;
  description?: string;
};

export function RawPayloadViewer({
  payload,
  title = "Raw payload",
  description = "Raw upstream evidence is preserved for auditability and debugging."
}: RawPayloadViewerProps) {
  const [expanded, setExpanded] = useState(false);
  const rawText = JSON.stringify(payload, null, 2);

  return (
    <EvidencePanel
      title={title}
      description={description}
      actions={
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setExpanded((value) => !value)}
        >
          {expanded ? "Collapse" : "Expand"}
        </Button>
      }
    >
      <pre className="overflow-x-auto rounded-panel border border-border-subtle bg-surface-base/70 p-4 text-left font-mono text-mono-sm text-content-secondary">
        {expanded ? rawText : `${rawText.slice(0, 420)}${rawText.length > 420 ? "\n..." : ""}`}
      </pre>
    </EvidencePanel>
  );
}
