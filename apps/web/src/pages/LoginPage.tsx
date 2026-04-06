import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { AegisCoreLogo } from "../components/AegisCoreLogo";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { authenticateOperator } from "../features/auth/service";
import { hasStoredAccessToken, isDevAuthBootstrapEnabled } from "../lib/api";

const devAuthBootstrapEnabled = isDevAuthBootstrapEnabled();
const defaultUsername = devAuthBootstrapEnabled
  ? import.meta.env.VITE_DEV_API_USERNAME ?? "admin"
  : "";

const defaultPassword = devAuthBootstrapEnabled
  ? import.meta.env.VITE_DEV_API_PASSWORD ?? "AegisCore123!"
  : "";

export function LoginPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState(defaultUsername);
  const [password, setPassword] = useState(defaultPassword);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (hasStoredAccessToken()) {
      navigate("/overview", { replace: true });
    }
  }, [navigate]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!username.trim() || !password.trim()) {
      setError("Username and password are required.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      await authenticateOperator(username.trim(), password);
      navigate("/overview", { replace: true });
    } catch (loginError: unknown) {
      setError(
        loginError instanceof Error ? loginError.message : "Sign-in failed."
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-shell">
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage:
            "radial-gradient(circle at top left, rgb(var(--color-brand-glow) / 0.24), transparent 32%), radial-gradient(circle at bottom right, rgb(var(--color-brand-primary) / 0.1), transparent 26%)"
        }}
      />
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(180deg,rgba(17,24,39,0.2),transparent_28%,rgba(10,10,10,0.65)_100%)]" />
      <div className="relative mx-auto grid min-h-screen max-w-7xl items-center gap-8 px-4 py-8 lg:grid-cols-[1.05fr_0.95fr] lg:px-8">
        <section className="space-y-6">
          <AegisCoreLogo titleAs="h1" className="items-start" />
          <div className="max-w-2xl space-y-4">
            <Badge tone="brand">Single-tenant SME SOC</Badge>
            <h2 className="type-display-lg text-content-primary">
              Sign in to AegisCore
            </h2>
            <p className="max-w-xl type-body-md">
              Access the operational dashboard, triage queue, incident workspace,
              automated-response policies, and reporting surfaces from one backend-owned
              SOC console.
            </p>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            {[
              {
                label: "In-scope detections",
                value: "4",
                detail:
                  "brute force, file integrity violation, port scan, and unauthorized user creation"
              },
              {
                label: "Core workflow",
                value: "Live",
                detail:
                  "ingestion, normalization, scoring, incident grouping, response, and reports"
              },
              {
                label: "Audit posture",
                value: "Tracked",
                detail:
                  "all workflow writes, notes, policies, and exports remain backend-audited"
              }
            ].map((item) => (
              <Card key={item.label} tone="subtle" className="border-border-subtle/85 bg-surface-subtle/55">
                <CardContent className="space-y-3 pt-6">
                  <p className="type-label-md">{item.label}</p>
                  <p className="type-heading-md">{item.value}</p>
                  <p className="type-body-sm">{item.detail}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        <Card className="mx-auto w-full max-w-xl border-brand-divider/45 bg-surface-panel/95 shadow-float">
          <CardHeader className="block space-y-3">
            <div className="space-y-2">
              <p className="type-label-md">Operator access</p>
              <CardTitle>Authenticate to the SOC console</CardTitle>
              <CardDescription>
                Sign in with a backend user account to open the live AegisCore
                operational surfaces.
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent className="space-y-5 pt-0">
            <form className="space-y-4" onSubmit={handleSubmit}>
              <Input
                label="Username"
                value={username}
                onChange={(event) => {
                  setUsername(event.target.value);
                  if (error) {
                    setError(null);
                  }
                }}
                autoComplete="username"
                placeholder="admin"
              />
              <Input
                label="Password"
                type="password"
                value={password}
                onChange={(event) => {
                  setPassword(event.target.value);
                  if (error) {
                    setError(null);
                  }
                }}
                autoComplete="current-password"
                placeholder="AegisCore password"
              />
              {error ? (
                <p className="text-body-sm text-status-danger">{error}</p>
              ) : import.meta.env.DEV ? (
                <p className="type-body-sm">
                  Local lab sign-in uses the seeded backend accounts. Automatic browser
                  bootstrap stays off unless
                  <span className="type-mono-sm"> VITE_ENABLE_DEV_AUTH_BOOTSTRAP=true</span>.
                </p>
              ) : (
                <p className="type-body-sm">
                  Authentication is handled by the backend JWT flow and stored locally
                  for this browser session.
                </p>
              )}
              <Button type="submit" variant="primary" fullWidth disabled={isSubmitting}>
                {isSubmitting ? "Signing in..." : "Sign in"}
              </Button>
            </form>

            {import.meta.env.DEV ? (
              <div className="rounded-panel border border-border-subtle bg-surface-subtle/55 p-4">
                <p className="type-label-sm">Local development shortcut</p>
                <p className="mt-2 type-body-sm">
                  Seeded credentials default to <span className="type-mono-sm">admin</span>{" "}
                  / <span className="type-mono-sm">AegisCore123!</span>.
                </p>
                <p className="mt-2 type-body-sm">
                  {devAuthBootstrapEnabled
                    ? "Dev auth bootstrap is currently enabled for local browser sessions."
                    : "Dev auth bootstrap is currently disabled, which keeps the login boundary explicit during local testing."}
                </p>
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
