/*
 * Search Input reusable UI component used by the React dashboard.
 */
import type { InputHTMLAttributes } from "react";
import { Input } from "./Input";
import { Icon } from "./Icon";

// Defines the Search Input Props data shape used by this frontend module.
type SearchInputProps = InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
  hint?: string;
};

// Renders the Search Input UI section.
export function SearchInput({ label, hint, ...props }: SearchInputProps) {
  return (
    <Input
      label={label}
      hint={hint}
      leadingVisual={<Icon name="search" className="h-4 w-4" />}
      placeholder="Search alerts, incidents, assets, or users"
      {...props}
    />
  );
}
