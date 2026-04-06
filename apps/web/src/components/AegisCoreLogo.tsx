import { cn } from "../lib/cn";

type AegisCoreLogoMode = "full" | "compact" | "mark";

type AegisCoreLogoProps = {
  mode?: AegisCoreLogoMode;
  titleAs?: "div" | "h1" | "h2";
  className?: string;
};

function AegisCoreMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 118 84"
      className={cn("h-full w-auto", className)}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path
        d="M16 72L50 14"
        stroke="rgb(var(--color-brand-ink))"
        strokeWidth="14"
        strokeLinecap="round"
      />
      <path
        d="M76 24L44 46H78L92 60H36"
        stroke="rgb(var(--color-brand-primary))"
        strokeWidth="14"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function AegisCoreAccent({ compact = false }: { compact?: boolean }) {
  return (
    <span
      className={cn(
        "mb-1 flex shrink-0 items-end gap-1",
        compact ? "pt-2" : "pt-3"
      )}
      aria-hidden="true"
    >
      <span
        className={cn(
          "block origin-bottom rounded-full bg-brand-ink",
          compact ? "h-5 w-2 rotate-[34deg]" : "h-6 w-2.5 rotate-[34deg]"
        )}
      />
      <span
        className={cn(
          "block origin-bottom rounded-full bg-brand-ink",
          compact ? "h-5 w-2 rotate-[34deg]" : "h-6 w-2.5 rotate-[34deg]"
        )}
      />
      <span
        className={cn(
          "mb-0.5 block rounded-full bg-brand-primary",
          compact ? "h-2.5 w-2.5" : "h-3 w-3"
        )}
      />
    </span>
  );
}

export function AegisCoreLogo({
  mode = "full",
  titleAs = "div",
  className
}: AegisCoreLogoProps) {
  const TitleTag = titleAs;
  const compact = mode === "compact";

  if (mode === "mark") {
    return (
      <div
        className={cn("flex items-center", className)}
        data-testid="aegiscore-logo-mark"
      >
        <div className="relative flex h-10 w-14 items-center justify-center overflow-hidden rounded-[1rem] border border-brand-divider/40 bg-surface-subtle/70 px-1 shadow-panel backdrop-blur">
          <div
            className="absolute inset-0"
            style={{
              backgroundImage:
                "radial-gradient(circle at 35% 35%, rgb(var(--color-brand-glow) / 0.24), transparent 58%)"
            }}
          />
          <div className="relative flex h-full items-center justify-center">
            <AegisCoreMark className="h-8" />
          </div>
        </div>
        <span className="sr-only">AegisCore</span>
      </div>
    );
  }

  return (
    <div
      className={cn("flex min-w-0 items-center gap-3", className)}
      data-testid="aegiscore-logo"
    >
      <div
        className={cn(
          "relative shrink-0 overflow-hidden rounded-[1.15rem] border border-brand-divider/35 bg-surface-subtle/70 shadow-panel backdrop-blur",
          compact ? "h-12 w-16 px-1.5" : "h-16 w-[5.5rem] px-2"
        )}
      >
        <div
          className="absolute inset-0"
          style={{
            backgroundImage:
              "radial-gradient(circle at 35% 35%, rgb(var(--color-brand-glow) / 0.24), transparent 58%)"
          }}
        />
        <div className="relative flex h-full items-center justify-center">
          <AegisCoreMark className={compact ? "h-8" : "h-11"} />
        </div>
      </div>
      <div className="flex min-w-0 items-center gap-3">
        <div
          className={cn(
            "hidden shrink-0 rounded-full bg-brand-divider/70 sm:block",
            compact ? "h-10 w-px" : "h-12 w-px"
          )}
          aria-hidden="true"
        />
        <div className="min-w-0">
          <p className={cn("type-label-sm text-content-muted", compact ? "mb-1" : "mb-2")}>
            {compact ? "SOC console" : "Security Operations"}
          </p>
          <div className="flex min-w-0 items-end gap-3">
            <TitleTag
              className={cn(
                "flex min-w-0 flex-col leading-none",
                compact ? "gap-0.5" : "gap-1"
              )}
              aria-label="AegisCore"
            >
              <span
                className={cn(
                  "truncate font-display font-semibold tracking-[0.18em] text-brand-ink",
                  compact ? "text-[0.82rem]" : "text-[1.05rem]"
                )}
              >
                AEGIS
              </span>
              <span
                className={cn(
                  "truncate font-display font-bold tracking-[0.22em] text-brand-primary",
                  compact ? "text-[1.35rem]" : "text-[1.85rem]"
                )}
              >
                CORE
              </span>
            </TitleTag>
            <AegisCoreAccent compact={compact} />
          </div>
          {!compact ? (
            <p className="mt-3 text-body-sm text-content-secondary">
              Single-tenant AI-assisted SOC console
            </p>
          ) : null}
        </div>
      </div>
    </div>
  );
}
