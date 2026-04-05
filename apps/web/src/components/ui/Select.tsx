import type { ReactNode, SelectHTMLAttributes } from "react";
import { cn } from "../../lib/cn";
import { Icon } from "./Icon";

type SelectOption = {
  label: string;
  value: string;
};

type SelectProps = SelectHTMLAttributes<HTMLSelectElement> & {
  label?: string;
  hint?: string;
  error?: string;
  options?: SelectOption[];
  placeholder?: string;
  prefix?: ReactNode;
};

export function Select({
  className,
  label,
  hint,
  error,
  options,
  placeholder,
  prefix,
  children,
  ...props
}: SelectProps) {
  return (
    <label className="flex w-full flex-col gap-3">
      {label ? <span className="type-label-sm text-content-secondary">{label}</span> : null}
      <span
        className={cn(
          "focus-within:shadow-focus relative flex h-11 items-center gap-3 rounded-field border bg-surface-subtle/75 px-3 transition",
          error ? "border-status-danger/60" : "border-border-subtle"
        )}
      >
        {prefix ? <span className="text-content-muted">{prefix}</span> : null}
        <select
          className={cn(
            "w-full appearance-none border-0 bg-transparent pr-8 text-body-md text-content-primary outline-none",
            className
          )}
          {...props}
        >
          {placeholder ? (
            <option value="" disabled>
              {placeholder}
            </option>
          ) : null}
          {options?.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
          {children}
        </select>
        <Icon
          name="chevron-right"
          className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 rotate-90 text-content-muted"
        />
      </span>
      {error ? (
        <span className="text-body-sm text-status-danger">{error}</span>
      ) : hint ? (
        <span className="text-body-sm text-content-muted">{hint}</span>
      ) : null}
    </label>
  );
}
