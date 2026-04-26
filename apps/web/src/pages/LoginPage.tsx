import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { AegisCoreLogo } from "../components/AegisCoreLogo";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { authenticateOperator } from "../features/auth/service";
import {
  hasStoredAccessToken,
  isDevAuthBootstrapEnabled,
  validateMfaAndPersistSession
} from "../lib/api";
import loginBg from "../assets/login-bg.png";

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
  const [mfaToken, setMfaToken] = useState<string | null>(null);
  const [totpCode, setTotpCode] = useState("");

  useEffect(() => {
    if (hasStoredAccessToken()) {
      navigate("/overview", { replace: true });
    }
  }, [navigate]);

  async function handlePasswordSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!username.trim() || !password.trim()) {
      setError("Username and password are required.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const result = await authenticateOperator(username.trim(), password);
      if ("mfa_required" in result && result.mfa_required) {
        setMfaToken(result.mfa_token);
        setTotpCode("");
        return;
      }
      navigate("/overview", { replace: true });
    } catch (loginError: unknown) {
      setError(
        loginError instanceof Error ? loginError.message : "Sign-in failed."
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleTotpSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!mfaToken) {
      return;
    }
    if (totpCode.trim().length !== 6) {
      setError("Enter the 6-digit code from your authenticator app.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      await validateMfaAndPersistSession(mfaToken, totpCode);
      navigate("/overview", { replace: true });
    } catch (loginError: unknown) {
      setError(
        loginError instanceof Error ? loginError.message : "MFA verification failed."
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div
      className="relative min-h-screen overflow-hidden bg-shell"
      style={{
        backgroundImage: `url(${loginBg})`,
        backgroundSize: "cover",
        backgroundPosition: "center top",
        backgroundRepeat: "no-repeat",
      }}
    >
      {/* Brand glow overlays */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage:
            "radial-gradient(circle at top left, rgb(var(--color-brand-glow) / 0.18), transparent 32%), radial-gradient(circle at bottom right, rgb(var(--color-brand-primary) / 0.08), transparent 26%)"
        }}
      />
      {/* Dark overlay so text remains readable over the background image */}
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(180deg,rgba(5,8,15,0.55),rgba(5,8,15,0.3)_40%,rgba(5,8,15,0.75)_100%)]" />

      <div className="relative mx-auto grid min-h-screen max-w-7xl items-start gap-8 px-4 py-16 lg:grid-cols-[1.05fr_0.95fr] lg:items-center lg:px-8 lg:py-8">
        <section className="space-y-6">
          <AegisCoreLogo titleAs="h1" className="items-start" />
          <div className="max-w-2xl space-y-4">
            <Badge tone="brand">Centralized SOC Platform</Badge>
            <h2 className="type-display-lg text-content-primary">
              Sign in to AegisCore
            </h2>
            <p className="max-w-xl type-body-md" style={{ color: "#f97316" }}>
              Access the operational dashboard, triage queue, incident workspace,
              automated-response policies, and reporting surfaces from one backend-owned
              SOC console.
            </p>
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
            {!mfaToken ? (
              <form className="space-y-4" onSubmit={handlePasswordSubmit}>
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
            ) : (
              <form className="space-y-4" onSubmit={handleTotpSubmit}>
                <p className="type-body-sm text-content-secondary">
                  Multi-factor authentication is enabled for this account. Open your
                  authenticator app and enter the current 6-digit code.
                </p>
                <Input
                  label="Authenticator code"
                  value={totpCode}
                  onChange={(event) => {
                    const v = event.target.value.replace(/\D/g, "").slice(0, 6);
                    setTotpCode(v);
                    if (error) {
                      setError(null);
                    }
                  }}
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  placeholder="000000"
                  maxLength={6}
                />
                {error ? (
                  <p className="text-body-sm text-status-danger">{error}</p>
                ) : null}
                <div className="flex flex-col gap-2 sm:flex-row">
                  <Button type="submit" variant="primary" fullWidth disabled={isSubmitting}>
                    {isSubmitting ? "Verifying…" : "Verify and continue"}
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    fullWidth
                    disabled={isSubmitting}
                    onClick={() => {
                      setMfaToken(null);
                      setTotpCode("");
                      setError(null);
                    }}
                  >
                    Back
                  </Button>
                </div>
              </form>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}