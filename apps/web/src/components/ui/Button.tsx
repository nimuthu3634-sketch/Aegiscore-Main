import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "../../lib/cn";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger" | "quiet";
type ButtonSize = "sm" | "md" | "lg" | "icon";

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
  leadingIcon?: ReactNode;
  trailingIcon?: ReactNode;
  fullWidth?: boolean;
};

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "border-brand-primary bg-brand-primary text-white hover:border-brand-hover hover:bg-brand-hover",
  secondary:
    "border-border-subtle bg-white text-content-primary hover:border-brand-primary/45 hover:bg-surface-subtle",
  ghost:
    "border-transparent bg-transparent text-content-secondary hover:bg-brand-primary/10 hover:text-brand-hover",
  danger:
    "border-status-danger/35 bg-status-danger/10 text-status-danger hover:bg-status-danger/16",
  quiet:
    "border-border-subtle bg-surface-subtle text-content-secondary hover:text-content-primary"
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: "h-9 px-3 text-label-sm",
  md: "h-10 px-4 text-label-md",
  lg: "h-11 px-5 text-label-md",
  icon: "h-10 w-10"
};

export function Button({
  className,
  variant = "secondary",
  size = "md",
  leadingIcon,
  trailingIcon,
  fullWidth = false,
  type = "button",
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        "focus-ring inline-flex items-center justify-center gap-2 rounded-field border font-semibold transition duration-150 disabled:pointer-events-none disabled:opacity-55",
        variantClasses[variant],
        sizeClasses[size],
        fullWidth && "w-full",
        className
      )}
      {...props}
    >
      {leadingIcon}
      {children}
      {trailingIcon}
    </button>
  );
}
