import type { InputHTMLAttributes, ReactNode } from "react";
import { cn } from "../../lib/cn";

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
  hint?: string;
  error?: string;
  leadingVisual?: ReactNode;
  trailingVisual?: ReactNode;
  mono?: boolean;
};

export function Input({
  className,
  label,
  hint,
  error,
  leadingVisual,
  trailingVisual,
  mono = false,
  id,
  ...props
}: InputProps) {
  return (
    <label className="flex w-full flex-col gap-3">
      {label ? <span className="type-label-sm text-content-secondary">{label}</span> : null}
      <span
        className={cn(
          "focus-within:shadow-focus flex h-11 items-center gap-3 rounded-field border bg-white px-3 transition",
          error ? "border-status-danger/60" : "border-border-subtle"
        )}
      >
        {leadingVisual ? (
          <span className="text-content-muted">{leadingVisual}</span>
        ) : null}
        <input
          id={id}
          className={cn(
            "w-full border-0 bg-transparent p-0 text-body-md text-content-primary outline-none placeholder:text-content-muted",
            mono && "font-mono text-mono-md",
            className
          )}
          {...props}
        />
        {trailingVisual ? (
          <span className="text-content-muted">{trailingVisual}</span>
        ) : null}
      </span>
      {error ? (
        <span className="text-body-sm text-status-danger">{error}</span>
      ) : hint ? (
        <span className="text-body-sm text-content-muted">{hint}</span>
      ) : null}
    </label>
  );
}
