import { cn } from "../lib/cn";

type AegisCoreLogoProps = {
  compact?: boolean;
  titleAs?: "div" | "h1" | "h2";
  className?: string;
};

export function AegisCoreLogo({
  compact = false,
  titleAs = "div",
  className
}: AegisCoreLogoProps) {
  const TitleTag = titleAs;

  return (
    <div className={cn("flex items-center gap-3", className)}>
      <div className="grid h-12 w-12 place-items-center rounded-[1rem] border border-brand-primary/30 bg-gradient-to-br from-brand-primary to-brand-hover shadow-panel">
        <span className="font-display text-sm font-bold tracking-[0.32em] text-content-primary">
          AC
        </span>
      </div>
      <div className="min-w-0">
        <p className="type-label-sm text-content-muted">
          Security Operations
        </p>
        <TitleTag
          className={cn(
            compact ? "type-heading-sm" : "type-heading-lg",
            "truncate"
          )}
        >
          AegisCore
        </TitleTag>
        {!compact ? (
          <p className="mt-1 text-body-sm text-content-secondary">
            Single-tenant AI-assisted SOC console
          </p>
        ) : null}
      </div>
    </div>
  );
}
