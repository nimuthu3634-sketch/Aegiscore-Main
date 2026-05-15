/*
 * Card reusable UI component used by the React dashboard.
 */
import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "../../lib/cn";

// Defines the Card Props data shape used by this frontend module.
type CardProps = HTMLAttributes<HTMLDivElement> & {
  tone?: "panel" | "raised" | "subtle";
};

// Renders the Card UI section.
export function Card({
  className,
  tone = "panel",
  ...props
}: CardProps) {
  return (
    <div
      className={cn(
        tone === "panel" && "panel-surface",
        tone === "raised" && "panel-raised",
        tone === "subtle" && "panel-subtle",
        className
      )}
      {...props}
    />
  );
}

// Defines the Card Section Props data shape used by this frontend module.
type CardSectionProps = {
  className?: string;
  children: ReactNode;
};

// Renders the Card Header UI section.
export function CardHeader({ className, children }: CardSectionProps) {
  return (
    <div className={cn("flex items-start justify-between gap-4 p-panel", className)}>
      {children}
    </div>
  );
}

// Renders the Card Title UI section.
export function CardTitle({ className, children }: CardSectionProps) {
  return <h3 className={cn("type-heading-sm", className)}>{children}</h3>;
}

// Renders the Card Description UI section.
export function CardDescription({ className, children }: CardSectionProps) {
  return <p className={cn("type-body-sm", className)}>{children}</p>;
}

// Renders the Card Content UI section.
export function CardContent({ className, children }: CardSectionProps) {
  return <div className={cn("px-panel pb-panel", className)}>{children}</div>;
}
