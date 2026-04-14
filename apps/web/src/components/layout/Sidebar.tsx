import { AegisCoreLogo } from "../AegisCoreLogo";
import type { NavigationItem, NavKey } from "../../lib/theme/tokens";
import { cn } from "../../lib/cn";
import { Button } from "../ui/Button";
import { Icon } from "../ui/Icon";

type SidebarProps = {
  items: NavigationItem[];
  activeId: NavKey;
  onNavigate: (id: NavKey) => void;
  onLogout: () => void;
  className?: string;
};

export function Sidebar({
  items,
  activeId,
  onNavigate,
  onLogout,
  className
}: SidebarProps) {
  return (
    <aside
      className={cn(
        "flex h-full flex-col gap-6 rounded-shell border border-[#151f30] bg-[#0f1726] p-4 text-slate-100 shadow-float",
        className
      )}
    >
      <div className="rounded-panel border border-slate-200/80 bg-white p-3.5">
        <AegisCoreLogo mode="compact" className="items-start" />
        <div className="mt-3 border-t border-slate-200 pt-3">
          <p className="type-label-sm text-slate-500">Environment</p>
          <p className="mt-1.5 text-body-sm text-slate-800">AegisCore SOC</p>
        </div>
      </div>
      <nav className="flex flex-1 flex-col gap-2" aria-label="Primary">
        <p className="px-2 type-label-sm text-slate-400">Operations</p>
        {items.map((item) => {
          const active = item.id === activeId;

          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onNavigate(item.id)}
              className={cn(
                "focus-ring flex items-center justify-between gap-3 rounded-panel border px-3 py-3 text-left transition-all duration-150",
                active
                  ? "border-brand-primary/45 bg-brand-primary/15 text-white shadow-[inset_3px_0_0_0_rgba(249,115,22,1),0_10px_20px_rgba(0,0,0,0.25)]"
                  : "border-transparent text-slate-300 hover:border-slate-600/70 hover:bg-slate-800/70 hover:text-white"
              )}
            >
              <span className="flex items-center gap-3">
                <Icon name={item.icon} className="h-4 w-4" />
                <span className="text-body-sm font-medium">{item.shortLabel}</span>
              </span>
              {item.badgeCount ? (
                <span className="inline-flex min-w-7 items-center justify-center rounded-full border border-slate-600/70 bg-slate-800/80 px-2 py-1 text-[0.6875rem] font-semibold text-slate-200">
                  {item.badgeCount}
                </span>
              ) : null}
            </button>
          );
        })}
      </nav>
      <div className="rounded-panel border border-slate-700/70 bg-slate-900/60 p-4">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="w-full justify-start border border-slate-600/60 text-slate-100 hover:border-brand-primary/45 hover:bg-brand-primary/15 hover:text-white"
          leadingIcon={<Icon name="logout" className="h-4 w-4" />}
          onClick={onLogout}
        >
          Log out
        </Button>
      </div>
    </aside>
  );
}