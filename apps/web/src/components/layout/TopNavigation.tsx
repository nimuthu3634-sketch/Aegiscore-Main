import type { ChangeEventHandler, ReactNode } from "react";
import type { HealthTone } from "../../lib/theme/tokens";
import { AegisCoreLogo } from "../AegisCoreLogo";
import { SearchInput } from "../ui/SearchInput";
import { Button } from "../ui/Button";
import { Icon } from "../ui/Icon";
import { Badge } from "../ui/Badge";

type TopNavigationProps = {
  healthTone: HealthTone;
  healthLabel: string;
  sessionLabel: string;
  sessionMfaEnabled: boolean;
  onSessionSecurityClick: () => void;
  searchValue: string;
  onSearchChange: ChangeEventHandler<HTMLInputElement>;
  onMenuClick: () => void;
  onLogout: () => void;
  /** Rendered between the health badge and MFA controls (e.g. notification bell). */
  notificationSlot?: ReactNode;
};

const healthToneMap: Record<HealthTone, "success" | "warning" | "danger"> = {
  healthy: "success",
  degraded: "warning",
  down: "danger"
};

export function TopNavigation({
  healthTone,
  healthLabel,
  sessionLabel,
  sessionMfaEnabled,
  onSessionSecurityClick,
  searchValue,
  onSearchChange,
  onMenuClick,
  onLogout,
  notificationSlot
}: TopNavigationProps) {
  return (
    <header className="sticky top-0 z-20 border-b border-border-subtle bg-white/92 backdrop-blur-xl">
      <div className="mx-auto flex max-w-shell items-center gap-3 px-4 py-4 md:px-6 lg:px-8">
        <div className="flex min-w-0 items-center gap-3">
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
        </div>
        <div className="min-w-0 flex-1">
          <SearchInput value={searchValue} onChange={onSearchChange} />
        </div>
        <div className="flex shrink-0 items-center gap-2 md:gap-3">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="text-content-secondary hover:text-brand-hover md:hidden"
            onClick={onSessionSecurityClick}
            aria-label="Account security and MFA"
          >
            <Icon name="shield" className="h-5 w-5" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onLogout}
            aria-label="Log out"
            className="text-content-secondary hover:text-brand-hover"
            leadingIcon={<Icon name="logout" className="h-4 w-4" />}
          >
            <span className="hidden sm:inline">Log out</span>
          </Button>
          <Badge
            tone={healthToneMap[healthTone]}
            icon={<Icon name="health" className="h-3.5 w-3.5" />}
            className="hidden md:inline-flex"
          >
            {healthLabel}
          </Badge>
          {notificationSlot ? (
            <div className="flex shrink-0 items-center">{notificationSlot}</div>
          ) : null}
          <div className="hidden items-center gap-2 md:flex">
            <Badge tone={sessionMfaEnabled ? "success" : "warning"}>
              MFA {sessionMfaEnabled ? "on" : "off"}
            </Badge>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              className="border-border-subtle bg-surface-subtle/80"
              leadingIcon={<Icon name="shield" className="h-4 w-4" />}
              onClick={onSessionSecurityClick}
            >
              {sessionLabel}
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}