import { startTransition, useEffect, useState } from "react";
import {
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate
} from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { AlertDetailPage } from "./pages/AlertDetailPage";
import { AlertsPage } from "./pages/AlertsPage";
import { AssetsPage } from "./pages/AssetsPage";
import { DashboardPage } from "./pages/DashboardPage";
import { IncidentDetailPage } from "./pages/IncidentDetailPage";
import { IncidentsPage } from "./pages/IncidentsPage";
import { ResponsesPage } from "./pages/ResponsesPage";
import { RulesPage } from "./pages/RulesPage";
import { fetchHealthResponse, type HealthResponse } from "./lib/api";
import {
  analystNavigation,
  pageBlueprints,
  type HealthTone,
  type NavKey
} from "./lib/theme/tokens";

function resolveActivePage(pathname: string): NavKey {
  const match = analystNavigation.find(
    (item) => pathname === item.path || pathname.startsWith(`${item.path}/`)
  );

  return match?.id ?? "overview";
}

export default function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [globalSearch, setGlobalSearch] = useState("");

  useEffect(() => {
    let isMounted = true;

    void fetchHealthResponse()
      .then((response) => {
        if (!isMounted) {
          return;
        }

        startTransition(() => {
          setHealth(response);
          setHealthError(null);
        });
      })
      .catch((error: Error) => {
        if (!isMounted) {
          return;
        }

        startTransition(() => {
          setHealth(null);
          setHealthError(error.message);
        });
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const activePage = resolveActivePage(location.pathname);
  const pageContent = pageBlueprints[activePage];

  const healthTone: HealthTone = healthError
    ? "down"
    : health?.database === "up"
      ? "healthy"
      : "degraded";

  const healthLabel = healthError
    ? "API connectivity issue"
    : health
      ? `API ${health.status} · database ${health.database}`
      : "Checking API health";

  return (
    <AppShell
      items={analystNavigation}
      activeId={activePage}
      onNavigate={(id) => {
        const target = analystNavigation.find((item) => item.id === id);

        if (target) {
          navigate(target.path);
        }
      }}
      pageTitle={pageContent.title}
      pageDescription={pageContent.description}
      healthTone={healthTone}
      healthLabel={healthLabel}
      searchValue={globalSearch}
      onSearchChange={(event) => setGlobalSearch(event.target.value)}
    >
      <Routes>
        <Route path="/" element={<Navigate to="/overview" replace />} />
        <Route path="/overview" element={<DashboardPage />} />
        <Route path="/alerts" element={<AlertsPage />} />
        <Route path="/alerts/:alertId" element={<AlertDetailPage />} />
        <Route path="/incidents" element={<IncidentsPage />} />
        <Route path="/incidents/:incidentId" element={<IncidentDetailPage />} />
        <Route path="/assets" element={<AssetsPage />} />
        <Route path="/responses" element={<ResponsesPage />} />
        <Route path="/rules" element={<RulesPage />} />
        <Route path="*" element={<Navigate to="/overview" replace />} />
      </Routes>
    </AppShell>
  );
}
