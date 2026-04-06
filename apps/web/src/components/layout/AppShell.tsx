import { useState } from "react";
import type { ChangeEventHandler, ReactNode } from "react";
import type {
  HealthTone,
  NavigationItem,
  NavKey
} from "../../lib/theme/tokens";
import { Sidebar } from "./Sidebar";
import { TopNavigation } from "./TopNavigation";

type AppShellProps = {
  items: NavigationItem[];
  activeId: NavKey;
  onNavigate: (id: NavKey) => void;
  pageTitle: string;
  pageDescription: string;
  healthTone: HealthTone;
  healthLabel: string;
  searchValue: string;
  onSearchChange: ChangeEventHandler<HTMLInputElement>;
  children: ReactNode;
};

export function AppShell({
  items,
  activeId,
  onNavigate,
  pageTitle,
  pageDescription,
  healthTone,
  healthLabel,
  searchValue,
  onSearchChange,
  children
}: AppShellProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleNavigate = (id: NavKey) => {
    onNavigate(id);
    setSidebarOpen(false);
  };

  return (
    <div className="relative min-h-screen bg-shell">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(249,115,22,0.14),transparent_34%),radial-gradient(circle_at_bottom_left,rgba(249,115,22,0.05),transparent_40%)]" />
      {sidebarOpen ? (
        <div
          className="fixed inset-0 z-40 bg-surface-overlay/45 px-4 py-4 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
          role="presentation"
        >
          <div onClick={(event) => event.stopPropagation()} role="presentation">
            <Sidebar items={items} activeId={activeId} onNavigate={handleNavigate} />
          </div>
        </div>
      ) : null}
      <div className="relative mx-auto min-h-screen max-w-shell lg:grid lg:grid-cols-shell">
        <div className="hidden px-3 py-3 lg:block">
          <Sidebar items={items} activeId={activeId} onNavigate={handleNavigate} />
        </div>
        <div className="min-w-0">
          <TopNavigation
            pageTitle={pageTitle}
            pageDescription={pageDescription}
            healthTone={healthTone}
            healthLabel={healthLabel}
            searchValue={searchValue}
            onSearchChange={onSearchChange}
            onMenuClick={() => setSidebarOpen(true)}
          />
          <main className="px-4 pb-8 pt-6 md:px-6 lg:px-8">
            <div className="mx-auto max-w-[76rem]">{children}</div>
          </main>
        </div>
      </div>
    </div>
  );
}
