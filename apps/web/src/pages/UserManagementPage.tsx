import { useState } from "react";
import { PageHeader } from "../components/layout/PageHeader";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Badge } from "../components/ui/Badge";
import { Icon } from "../components/ui/Icon";
import { getStoredSessionRole } from "../lib/api";
import { createUser } from "../features/users/service";
import type { CreateUserPayload, UserRecord, UserRole } from "../features/users/types";

type RoleOption = { value: UserRole; label: string; description: string };

const roleOptions: RoleOption[] = [
  {
    value: "analyst",
    label: "Analyst",
    description: "Investigation, reporting, alerts, incidents, responses, assets, dashboard.",
  },
  {
    value: "admin",
    label: "Admin",
    description: "Full access including policy management and manual ingestion.",
  },
];

export function UserManagementPage() {
  const sessionRole = getStoredSessionRole();
  const isAdmin = sessionRole === "admin";

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState<UserRole>("analyst");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [createdUsers, setCreatedUsers] = useState<UserRecord[]>([]);

  function resetForm() {
    setUsername("");
    setPassword("");
    setFullName("");
    setRole("analyst");
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setSuccessMessage(null);

    if (!username.trim()) {
      setError("Username is required.");
      return;
    }

    if (username.trim().length < 3) {
      setError("Username must be at least 3 characters.");
      return;
    }

if (!/^[a-zA-Z0-9_-]+$/.test(username.trim())) {      setError("Username may only contain letters, numbers, hyphens, and underscores.");
      return;
    }

    if (!password) {
      setError("Password is required.");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    const payload: CreateUserPayload = {
      username: username.trim(),
      password,
      role,
    };

    if (fullName.trim()) {
      payload.full_name = fullName.trim();
    }

    setIsSubmitting(true);

    try {
      const response = await createUser(payload);
      setSuccessMessage(response.message);
      setCreatedUsers((prev) => [response.user, ...prev]);
      resetForm();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unexpected error occurred.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  if (!isAdmin) {
    return (
      <div className="space-y-section">
        <PageHeader
          eyebrow="Administration"
          title="User Management"
          description="Only administrators can create new user accounts."
        />
        <Card>
          <CardContent className="py-12 text-center">
            <Icon name="shield" className="mx-auto mb-4 h-10 w-10 text-content-muted" />
            <p className="type-heading-sm text-content-secondary">
              Admin role required
            </p>
            <p className="mt-2 type-body-sm text-content-muted">
              You do not have permission to manage users. Contact an administrator.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-section">
      <PageHeader
        eyebrow="Administration"
        title="User Management"
        description="Create new SOC operator accounts for analysts and administrators."
      />

      <div className="grid gap-section lg:grid-cols-5">
        {/* ── Create user form ───────────────────────────────────── */}
        <div className="lg:col-span-3">
          <Card>
            <CardHeader className="block space-y-2">
              <CardTitle>Create new user</CardTitle>
              <CardDescription>
                New accounts are active immediately after creation. Users can sign
                in using the credentials set here.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5 pt-0">
              <form className="space-y-4" onSubmit={handleSubmit}>
                <Input
                  label="Username"
                  value={username}
                  onChange={(e) => {
                    setUsername(e.target.value);
                    if (error) setError(null);
                  }}
                  placeholder="new-analyst"
                  autoComplete="off"
                  hint="3–50 characters. Letters, numbers, hyphens, and underscores only."
                />

                <Input
                  label="Full Name"
                  value={fullName}
                  onChange={(e) => {
                    setFullName(e.target.value);
                    if (error) setError(null);
                  }}
                  placeholder="Jane Doe"
                  autoComplete="off"
                  hint="Optional display name shown across the SOC console."
                />

                <Input
                  label="Password"
                  type="password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (error) setError(null);
                  }}
                  placeholder="Minimum 8 characters"
                  autoComplete="new-password"
                />

                {/* ── Role selector ────────────────────────────────── */}
                <div className="space-y-3">
                  <span className="type-label-sm text-content-secondary">Role</span>
                  <div className="grid gap-3 sm:grid-cols-2">
                    {roleOptions.map((option) => {
                      const isSelected = role === option.value;
                      return (
                        <button
                          key={option.value}
                          type="button"
                          onClick={() => {
                            setRole(option.value);
                            if (error) setError(null);
                          }}
                          className={[
                            "rounded-panel border px-4 py-3 text-left transition",
                            isSelected
                              ? "border-brand-primary/60 bg-brand-primary/8 shadow-sm"
                              : "border-border-subtle bg-white hover:border-brand-primary/30 hover:bg-surface-subtle",
                          ].join(" ")}
                        >
                          <span className="type-label-sm text-content-primary">
                            {option.label}
                          </span>
                          <p className="mt-1 text-body-sm text-content-muted">
                            {option.description}
                          </p>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* ── Feedback ─────────────────────────────────────── */}
                {error ? (
                  <p className="text-body-sm text-status-danger">{error}</p>
                ) : successMessage ? (
                  <p className="text-body-sm text-status-success">{successMessage}</p>
                ) : null}

                <Button
                  type="submit"
                  variant="primary"
                  fullWidth
                  disabled={isSubmitting}
                >
                  {isSubmitting ? "Creating account..." : "Create user"}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* ── Recently created sidebar ────────────────────────────── */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader className="block space-y-2">
              <CardTitle>Recently created</CardTitle>
              <CardDescription>
                Users created in this session.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-0">
              {createdUsers.length === 0 ? (
                <div className="py-8 text-center">
                  <Icon name="shield" className="mx-auto mb-3 h-8 w-8 text-content-muted" />
                  <p className="type-body-sm text-content-muted">
                    No users created yet.
                  </p>
                </div>
              ) : (
                <ul className="divide-y divide-border-subtle">
                  {createdUsers.map((user) => (
                    <li key={user.id} className="flex items-center justify-between py-3">
                      <div className="min-w-0">
                        <p className="type-label-sm text-content-primary truncate">
                          {user.full_name || user.username}
                        </p>
                        <p className="text-body-sm text-content-muted">
                          @{user.username}
                        </p>
                      </div>
                      <Badge tone={user.role.name === "admin" ? "warning" : "brand"}>
                        {user.role.name}
                      </Badge>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}