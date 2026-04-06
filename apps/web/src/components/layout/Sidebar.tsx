import { AegisCoreLogo } from "../AegisCoreLogo";
import type { NavigationItem, NavKey } from "../../lib/theme/tokens";
import { cn } from "../../lib/cn";
import { Button } from "../ui/Button";
import { Icon } from "../ui/Icon";

type SidebarProps = {
  items: NavigationItem[];
  activeId: NavKey;
  onNavigate: (id: NavKey) => void;
  className?: string;
};

export function Sidebar({
  items,
  activeId,
  onNavigate,
  className
}: SidebarProps) {
  return (
    <aside
      className={cn(
        "flex h-full flex-col gap-6 rounded-shell border border-border-subtle bg-surface-panel/95 p-4 shadow-float backdrop-blur",
        className
      )}
    >
      <AegisCoreLogo mode="compact" className="items-start" />
      <div className="rounded-panel border border-brand-divider/45 bg-surface-subtle/65 px-4 py-3">
        <p className="type-label-sm">Environment</p>
        <p className="mt-2 text-body-sm text-content-primary">Single-tenant SME SOC</p>
      </div>
      <nav className="flex flex-1 flex-col gap-2" aria-label="Primary">
        {items.map((item) => {
          const active = item.id === activeId;

          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onNavigate(item.id)}
              className={cn(
                "focus-ring flex items-center justify-between gap-3 rounded-panel border px-3 py-3 text-left transition",
                active
                  ? "border-brand-primary/40 bg-surface-accentSoft text-content-primary shadow-[inset_3px_0_0_0_rgba(249,115,22,1)]"
                  : "border-transparent text-content-secondary hover:border-brand-divider/45 hover:bg-surface-subtle/65 hover:text-content-primary"
              )}
            >
              <span className="flex items-center gap-3">
                <Icon name={item.icon} className="h-4 w-4" />
                <span className="text-body-sm font-medium">{item.shortLabel}</span>
              </span>
              {item.badgeCount ? (
                <span className="inline-flex min-w-7 items-center justify-center rounded-full border border-border-subtle px-2 py-1 text-[0.6875rem] font-semibold text-content-muted">
                  {item.badgeCount}
                </span>
              ) : null}
            </button>
          );
        })}
      </nav>
      <div className="rounded-panel border border-brand-divider/45 bg-surface-subtle/65 p-4">
        <p className="type-label-sm">Backend ownership</p>
        <p className="mt-2 text-body-sm text-content-secondary">
          Wazuh and Suricata remain behind the API boundary. The UI consumes backend-only contracts.
        </p>
        <Button
          variant="ghost"
          size="sm"
          className="mt-4 justify-start px-0 text-content-primary"
          trailingIcon={<Icon name="chevron-right" className="h-4 w-4" />}
        >
          Review platform scope
        </Button>
      </div>
    </aside>
  );
}
