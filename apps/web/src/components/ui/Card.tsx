import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "../../lib/cn";

type CardProps = HTMLAttributes<HTMLDivElement> & {
  tone?: "panel" | "raised" | "subtle";
};

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

type CardSectionProps = {
  className?: string;
  children: ReactNode;
};

export function CardHeader({ className, children }: CardSectionProps) {
  return (
    <div className={cn("flex items-start justify-between gap-4 p-panel", className)}>
      {children}
    </div>
  );
}

export function CardTitle({ className, children }: CardSectionProps) {
  return <h3 className={cn("type-heading-sm", className)}>{children}</h3>;
}

export function CardDescription({ className, children }: CardSectionProps) {
  return <p className={cn("type-body-sm", className)}>{children}</p>;
}

export function CardContent({ className, children }: CardSectionProps) {
  return <div className={cn("px-panel pb-panel", className)}>{children}</div>;
}
