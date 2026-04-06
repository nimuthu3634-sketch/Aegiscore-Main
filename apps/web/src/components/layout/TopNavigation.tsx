import type { ChangeEventHandler } from "react";
import type { HealthTone } from "../../lib/theme/tokens";
import { AegisCoreLogo } from "../AegisCoreLogo";
import { SearchInput } from "../ui/SearchInput";
import { Button } from "../ui/Button";
import { Icon } from "../ui/Icon";
import { Badge } from "../ui/Badge";

type TopNavigationProps = {
  pageTitle: string;
  pageDescription: string;
  healthTone: HealthTone;
  healthLabel: string;
  searchValue: string;
  onSearchChange: ChangeEventHandler<HTMLInputElement>;
  onMenuClick: () => void;
};

const healthToneMap: Record<HealthTone, "success" | "warning" | "danger"> = {
  healthy: "success",
  degraded: "warning",
  down: "danger"
};

export function TopNavigation({
  pageTitle,
  pageDescription,
  healthTone,
  healthLabel,
  searchValue,
  onSearchChange,
  onMenuClick
}: TopNavigationProps) {
  return (
    <header className="sticky top-0 z-20 border-b border-border-subtle bg-surface-base/70 backdrop-blur">
      <div className="mx-auto flex max-w-shell items-center gap-3 px-4 py-4 md:px-6 lg:px-8">
        <div className="flex min-w-0 flex-1 items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={onMenuClick}
            aria-label="Open navigation"
          >
            <Icon name="menu" className="h-5 w-5" />
          </Button>
          <AegisCoreLogo mode="mark" className="shrink-0 sm:hidden" />
          <AegisCoreLogo mode="compact" className="hidden max-w-[14.5rem] shrink-0 sm:flex" />
          <div className="min-w-0 flex-1 border-l border-brand-divider/60 pl-3 sm:pl-4">
            <p className="type-label-sm hidden md:block">{pageTitle}</p>
            <p className="truncate text-body-sm text-content-secondary">{pageDescription}</p>
          </div>
        </div>
        <div className="hidden min-w-[20rem] flex-1 xl:block">
          <SearchInput value={searchValue} onChange={onSearchChange} />
        </div>
        <div className="hidden items-center gap-3 md:flex">
          <Badge tone={healthToneMap[healthTone]} icon={<Icon name="health" className="h-3.5 w-3.5" />}>
            {healthLabel}
          </Badge>
          <Button variant="secondary" size="sm" leadingIcon={<Icon name="shield" className="h-4 w-4" />}>
            Analyst session
          </Button>
        </div>
      </div>
    </header>
  );
}
