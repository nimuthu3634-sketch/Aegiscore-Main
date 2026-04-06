import type { CSSProperties } from "react";
import { cn } from "../lib/cn";

type AegisCoreLogoMode = "full" | "compact" | "mark";

type AegisCoreLogoProps = {
  mode?: AegisCoreLogoMode;
  titleAs?: "div" | "h1" | "h2";
  className?: string;
};

const aegisWordStyle: CSSProperties = {
  color: "rgb(var(--color-brand-ink))",
  fontFamily: '"Orbitron", "Space Grotesk", sans-serif',
  WebkitTextFillColor: "transparent",
  WebkitTextStroke: "1.4px rgb(var(--color-brand-ink))"
};

const coreWordStyle: CSSProperties = {
  fontFamily: '"Saira Stencil One", "Space Grotesk", sans-serif'
};

function AegisCoreMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 440 320"
      className={cn("h-full w-auto", className)}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path
        d="M48 280L166 44"
        stroke="rgb(var(--color-brand-ink))"
        strokeWidth="46"
        strokeLinecap="round"
      />
      <path
        d="M244 78L160 158H308L388 266H148"
        stroke="rgb(var(--color-brand-primary))"
        strokeWidth="46"
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
        "mb-0.5 flex shrink-0 items-end",
        compact ? "gap-1 pt-1" : "gap-1.5 pt-1.5"
      )}
      aria-hidden="true"
    >
      <span
        className={cn(
          "block origin-bottom rounded-full bg-brand-ink",
          compact ? "h-4 w-1.5 rotate-[32deg]" : "h-5 w-2 rotate-[32deg]"
        )}
      />
      <span
        className={cn(
          "block origin-bottom rounded-full bg-brand-ink",
          compact ? "h-4 w-1.5 rotate-[32deg]" : "h-5 w-2 rotate-[32deg]"
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
        <AegisCoreMark className="h-10" />
        <span className="sr-only">AegisCore</span>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex min-w-0 items-center",
        compact ? "gap-2.5" : "gap-3.5",
        className
      )}
      data-testid="aegiscore-logo"
    >
      <AegisCoreMark className={compact ? "h-10 sm:h-11" : "h-14 sm:h-16"} />
      <div
        className={cn(
          "hidden shrink-0 rounded-full bg-brand-divider/80 sm:block",
          compact ? "h-9 w-px" : "h-12 w-px"
        )}
        aria-hidden="true"
      />
      <TitleTag
        className={cn(
          "flex min-w-0 items-end leading-none",
          compact ? "gap-2" : "gap-3"
        )}
        aria-label="AegisCore"
      >
        <span className="flex min-w-0 flex-col whitespace-nowrap">
          <span
            className={cn(
              "block leading-none tracking-[0.16em]",
              compact ? "text-[0.82rem]" : "text-[1.02rem] sm:text-[1.15rem]"
            )}
            style={aegisWordStyle}
          >
            AEGIS
          </span>
          <span
            className={cn(
              "mt-1 block leading-none tracking-[0.12em] text-brand-primary",
              compact ? "text-[1.5rem]" : "text-[1.9rem] sm:text-[2.15rem]"
            )}
            style={coreWordStyle}
          >
            CORE
          </span>
        </span>
        <AegisCoreAccent compact={compact} />
      </TitleTag>
    </div>
  );
}
