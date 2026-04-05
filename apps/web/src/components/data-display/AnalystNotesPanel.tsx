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
  draft: string;
  onDraftChange: (value: string) => void;
  onSave: () => void;
  isSaving?: boolean;
  saveError?: string | null;
  saveSuccess?: string | null;
  saveDisabled?: boolean;
};

export function AnalystNotesPanel({
  notes,
  composerLabel = "Add analyst note",
  draft,
  onDraftChange,
  onSave,
  isSaving = false,
  saveError,
  saveSuccess,
  saveDisabled = false
}: AnalystNotesPanelProps) {
  return (
    <EvidencePanel
      title="Analyst notes"
      description="Persisted analyst notes tied directly to the current investigation record."
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
            value={draft}
            onChange={(event) => onDraftChange(event.target.value)}
          />
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="min-h-[1.25rem]">
              {saveError ? (
                <p className="text-body-sm text-status-danger">{saveError}</p>
              ) : saveSuccess ? (
                <p className="text-body-sm text-status-success">{saveSuccess}</p>
              ) : null}
            </div>
            <Button
              variant="secondary"
              size="sm"
              onClick={onSave}
              disabled={isSaving || saveDisabled}
            >
              {isSaving ? "Saving note..." : "Save note"}
            </Button>
          </div>
        </div>
      </div>
    </EvidencePanel>
  );
}
