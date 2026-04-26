import { startTransition, useCallback, useEffect, useState } from "react";
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
import { MfaSetupModal } from "./features/auth/MfaSetupModal";
import { LoginPage } from "./pages/LoginPage";
import { ReportsPage } from "./pages/ReportsPage";
import { ResponsesPage } from "./pages/ResponsesPage";
import { RulesPage } from "./pages/RulesPage";
import { UserManagementPage } from "./pages/UserManagementPage";
import {
  AUTH_REQUIRED_EVENT,
  fetchCurrentUser,
  fetchHealthResponse,
  getStoredSessionRole,
  getStoredUsername,
  hasStoredAccessToken,
  isDevAuthBootstrapEnabled,
  logoutOperator,
  type AuthUserResponse,
  type HealthResponse
} from "./lib/api";
import {
  analystNavigation,
  primaryNavigation,
  pageBlueprints,
  type HealthTone,
  type NavKey
} from "./lib/theme/tokens";

function resolveActivePage(pathname: string): NavKey {
  const match = primaryNavigation.find(
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
  const [sessionProfile, setSessionProfile] = useState<AuthUserResponse | null>(null);
  const [securityModalOpen, setSecurityModalOpen] = useState(false);
  const isLoginRoute = location.pathname === "/login";
  const hasSession = hasStoredAccessToken();
  const allowDevBootstrap = isDevAuthBootstrapEnabled();
  const sessionRole = getStoredSessionRole();
  const storedUsername = getStoredUsername();
  const sessionLabel = storedUsername
    ? storedUsername
    : sessionRole === "admin"
      ? "Admin"
      : sessionRole === "analyst"
        ? "Analyst"
        : "Session";

  const refreshSessionProfile = useCallback(() => {
    void fetchCurrentUser()
      .then((user) => {
        setSessionProfile(user);
      })
      .catch(() => {
        setSessionProfile(null);
      });
  }, []);

  useEffect(() => {
    if (isLoginRoute) {
      return undefined;
    }

    let isMounted = true;

    void fetchCurrentUser()
      .then((user) => {
        if (!isMounted) {
          return;
        }
        setSessionProfile(user);
      })
      .catch(() => {
        if (!isMounted) {
          return;
        }
        setSessionProfile(null);
      });

    return () => {
      isMounted = false;
    };
  }, [isLoginRoute, hasSession, allowDevBootstrap, location.pathname]);

  useEffect(() => {
    if (isLoginRoute) {
      return undefined;
    }

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
  }, [isLoginRoute]);

  useEffect(() => {
    if (isLoginRoute || typeof window === "undefined") {
      return undefined;
    }

    const handleAuthRequired = () => {
      navigate("/login", { replace: true });
    };

    window.addEventListener(AUTH_REQUIRED_EVENT, handleAuthRequired);

    return () => {
      window.removeEventListener(AUTH_REQUIRED_EVENT, handleAuthRequired);
    };
  }, [isLoginRoute, navigate]);

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

  function handleLogout() {
    logoutOperator();
    setSessionProfile(null);
    navigate("/login", { replace: true });
  }

  if (isLoginRoute) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  if (!hasSession && !allowDevBootstrap) {
    return <Navigate to="/login" replace />;
  }

  const sidebarItems =
    sessionRole === "admin"
      ? [...analystNavigation, ...primaryNavigation.filter((i) => i.id === "users")]
      : analystNavigation;

  return (
    <>
      <MfaSetupModal
        open={securityModalOpen}
        onClose={() => setSecurityModalOpen(false)}
        mfaEnabled={sessionProfile?.mfa_enabled ?? false}
        isAdmin={sessionProfile?.role.name === "admin"}
        onProfileChanged={refreshSessionProfile}
      />
      <AppShell
        items={sidebarItems}
        activeId={activePage}
        onNavigate={(id) => {
          const target = primaryNavigation.find((item) => item.id === id);

          if (target) {
            navigate(target.path);
          }
        }}
        onLogout={handleLogout}
        pageTitle={pageContent.title}
        pageDescription={pageContent.description}
        healthTone={healthTone}
        healthLabel={healthLabel}
        sessionLabel={sessionLabel}
        sessionMfaEnabled={sessionProfile?.mfa_enabled ?? false}
        onSessionSecurityClick={() => setSecurityModalOpen(true)}
        searchValue={globalSearch}
        onSearchChange={(event) => setGlobalSearch(event.target.value)}
      >
        <Routes>
          <Route path="/" element={<Navigate to="/overview" replace />} />
          <Route path="/login" element={<Navigate to="/overview" replace />} />
          <Route path="/overview" element={<DashboardPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/alerts/:alertId" element={<AlertDetailPage />} />
          <Route path="/incidents" element={<IncidentsPage />} />
          <Route path="/incidents/:incidentId" element={<IncidentDetailPage />} />
          <Route path="/assets" element={<AssetsPage />} />
          <Route path="/responses" element={<ResponsesPage />} />
          <Route path="/rules" element={<RulesPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/users" element={<UserManagementPage />} />
          <Route path="*" element={<Navigate to="/overview" replace />} />
        </Routes>
      </AppShell>
    </>
  );
}