import { Button } from "../ui/Button";
import { Textarea } from "../ui/Textarea";
import { EvidencePanel } from "./EvidencePanel";

export type AnalystNote = {
  id: string;
  author: string;
  timestamp: string;
  content: string;
};

type AnalystNotesPanelProps = {
  notes: AnalystNote[];
  composerLabel?: string;
};

export function AnalystNotesPanel({
  notes,
  composerLabel = "Add analyst note"
}: AnalystNotesPanelProps) {
  return (
    <EvidencePanel
      title="Analyst notes"
      description="Dense note-taking space prepared for future save and collaboration APIs."
    >
      <div className="space-y-4">
        {notes.length ? (
          <div className="space-y-3">
            {notes.map((note) => (
              <div
                key={note.id}
                className="rounded-panel border border-border-subtle bg-surface-subtle/65 p-4"
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <p className="text-body-sm font-medium text-content-primary">
                    {note.author}
                  </p>
                  <p className="type-mono-sm">{note.timestamp}</p>
                </div>
                <p className="mt-3 type-body-sm">{note.content}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-panel border border-dashed border-border-subtle bg-surface-base/30 p-4">
            <p className="type-body-sm">
              No analyst notes have been captured yet for this investigation.
            </p>
          </div>
        )}
        <div className="space-y-3 rounded-panel border border-border-subtle bg-surface-base/40 p-4">
          <Textarea
            label={composerLabel}
            placeholder="Capture investigation context, escalation notes, or follow-up tasks."
          />
          <div className="flex justify-end">
            <Button variant="secondary" size="sm">
              Save note placeholder
            </Button>
          </div>
        </div>
      </div>
    </EvidencePanel>
  );
}
