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
  onLogout: () => void;
  pageTitle: string;
  pageDescription: string;
  healthTone: HealthTone;
  healthLabel: string;
  sessionLabel: string;
  sessionMfaEnabled: boolean;
  onSessionSecurityClick: () => void;
  searchValue: string;
  onSearchChange: ChangeEventHandler<HTMLInputElement>;
  children: ReactNode;
};

export function AppShell({
  items,
  activeId,
  onNavigate,
  onLogout,
  pageTitle,
  pageDescription,
  healthTone,
  healthLabel,
  sessionLabel,
  sessionMfaEnabled,
  onSessionSecurityClick,
  searchValue,
  onSearchChange,
  children
}: AppShellProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleNavigate = (id: NavKey) => {
    onNavigate(id);
    setSidebarOpen(false);
  };

  const handleLogout = () => {
    setSidebarOpen(false);
    onLogout();
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
            <Sidebar
              items={items}
              activeId={activeId}
              onNavigate={handleNavigate}
              onLogout={handleLogout}
            />
          </div>
        </div>
      ) : null}
      <div className="relative mx-auto min-h-screen max-w-shell lg:grid lg:grid-cols-shell">
        <div className="hidden px-3 py-3 lg:block">
          <Sidebar
            items={items}
            activeId={activeId}
            onNavigate={handleNavigate}
            onLogout={handleLogout}
          />
        </div>
        <div className="min-w-0">
          <TopNavigation
            pageTitle={pageTitle}
            pageDescription={pageDescription}
            healthTone={healthTone}
            healthLabel={healthLabel}
            sessionLabel={sessionLabel}
            sessionMfaEnabled={sessionMfaEnabled}
            onSessionSecurityClick={onSessionSecurityClick}
            searchValue={searchValue}
            onSearchChange={onSearchChange}
            onMenuClick={() => setSidebarOpen(true)}
            onLogout={handleLogout}
          />
          <main className="px-4 pb-8 pt-6 md:px-6 lg:px-8">
            <div className="mx-auto max-w-[76rem]">{children}</div>
          </main>
          <footer className="border-t border-border-subtle/40 px-4 py-4 md:px-6 lg:px-8">
            <div className="mx-auto flex max-w-[76rem] flex-wrap items-center justify-between gap-2">
              <p className="type-body-sm text-content-muted">AegisCore SOC Platform &mdash; v1.0.0</p>
              <p className="type-body-sm text-content-muted">Powered by Wazuh &amp; Suricata &middot; AI by TensorFlow</p>
            </div>
          </footer>
        </div>
      </div>
    </div>
  );
}