import { cn } from "../lib/cn";

type AegisCoreLogoMode = "full" | "compact" | "mark";

type AegisCoreLogoProps = {
  mode?: AegisCoreLogoMode;
  titleAs?: "div" | "h1" | "h2";
  className?: string;
};

export function AegisCoreLogo({
  mode = "full",
  titleAs = "div",
  className
}: AegisCoreLogoProps) {
  const TitleTag = titleAs;

  if (mode === "mark") {
    return (
      <div
        className={cn("flex items-center", className)}
        data-testid="aegiscore-logo-mark"
      >
        <img
          src="/brand/aegiscore-mark.svg"
          alt="AegisCore emblem"
          className="h-10 w-auto object-contain"
          loading="eager"
          decoding="async"
        />
        <span className="sr-only">AegisCore</span>
      </div>
    );
  }

  return (
    <TitleTag
      className={cn("flex items-center", className)}
      data-testid="aegiscore-logo"
      aria-label="AegisCore"
    >
      <img
        src="/brand/aegiscore-logo.svg"
        alt="AegisCore logo"
        className={cn(
          "w-auto object-contain",
          mode === "compact" ? "h-11 sm:h-12" : "h-16 sm:h-[4.5rem]"
        )}
        loading="eager"
        decoding="async"
      />
    </TitleTag>
  );
}
