import type { InputHTMLAttributes } from "react";
import { Input } from "./Input";
import { Icon } from "./Icon";

type SearchInputProps = InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
  hint?: string;
};

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
