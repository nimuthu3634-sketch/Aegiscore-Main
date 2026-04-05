import type { TextareaHTMLAttributes } from "react";
import { cn } from "../../lib/cn";

type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement> & {
  label?: string;
  hint?: string;
  error?: string;
  mono?: boolean;
};

export function Textarea({
  className,
  label,
  hint,
  error,
  mono = false,
  ...props
}: TextareaProps) {
  return (
    <label className="flex w-full flex-col gap-3">
      {label ? <span className="type-label-sm text-content-secondary">{label}</span> : null}
      <textarea
        className={cn(
          "focus-ring min-h-[120px] w-full rounded-field border bg-surface-subtle/75 px-4 py-3 text-body-md text-content-primary placeholder:text-content-muted",
          error ? "border-status-danger/60" : "border-border-subtle",
          mono && "font-mono text-mono-md",
          className
        )}
        {...props}
      />
      {error ? (
        <span className="text-body-sm text-status-danger">{error}</span>
      ) : hint ? (
        <span className="text-body-sm text-content-muted">{hint}</span>
      ) : null}
    </label>
  );
}
