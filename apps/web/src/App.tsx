import { startTransition, useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { AegisCoreLogo } from "./components/AegisCoreLogo";
import { fetchHealthResponse, type HealthResponse } from "./lib/api";

const alertActivity = [
  { detectionType: "brute_force", alerts: 16 },
  { detectionType: "file_integrity_violation", alerts: 6 },
  { detectionType: "port_scan", alerts: 12 },
  { detectionType: "unauthorized_user_creation", alerts: 3 }
];

const dashboardCards = [
  {
    label: "Normalized Alerts",
    value: "37",
    detail: "Wazuh and Suricata ingestion pipeline target"
  },
  {
    label: "Active Incidents",
    value: "4",
    detail: "Investigation queue prepared for analyst workflows"
  },
  {
    label: "Response Policies",
    value: "3",
    detail: "Basic automated actions reserved for SME-safe workflows"
  }
];

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);

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

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(249,115,22,0.22),_transparent_28%),linear-gradient(180deg,_#111827_0%,_#0A0A0A_52%,_#050505_100%)] text-aegis-text">
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col gap-8 px-6 py-8 lg:px-10">
        <header className="flex flex-col gap-6 rounded-3xl border border-aegis-border bg-[rgba(17,24,39,0.78)] p-6 shadow-panel backdrop-blur md:flex-row md:items-center md:justify-between">
          <AegisCoreLogo />
          <div className="flex flex-col gap-3 md:items-end">
            <div className="inline-flex items-center gap-2 rounded-full border border-aegis-border bg-black/30 px-4 py-2 text-sm text-aegis-soft">
              <span
                className={`h-2.5 w-2.5 rounded-full ${
                  health?.database === "up"
                    ? "bg-aegis-success"
                    : "bg-aegis-warning"
                }`}
              />
              {health
                ? `API ${health.status} | database ${health.database}`
                : healthError ?? "Waiting for backend health"}
            </div>
            <p className="max-w-xl text-sm text-aegis-muted">
              Centralized monitoring, alert prioritization, investigation, and
              controlled response workflows for SME security teams.
            </p>
          </div>
        </header>

        <main className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <section className="rounded-3xl border border-aegis-border bg-[rgba(17,24,39,0.82)] p-6 shadow-panel">
            <div className="mb-6 flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.35em] text-aegis-muted">
                  Detection Focus
                </p>
                <h2 className="mt-2 text-2xl font-semibold text-aegis-text">
                  In-Scope Security Activity
                </h2>
              </div>
              <span className="rounded-full border border-aegis-border px-3 py-1 text-xs uppercase tracking-[0.3em] text-aegis-soft">
                Single tenant
              </span>
            </div>

            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={alertActivity}>
                  <defs>
                    <linearGradient id="alertFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#F97316" stopOpacity={0.55} />
                      <stop offset="95%" stopColor="#F97316" stopOpacity={0.05} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="#1F2937" strokeDasharray="4 4" />
                  <XAxis dataKey="detectionType" stroke="#9CA3AF" />
                  <YAxis stroke="#9CA3AF" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#111827",
                      borderColor: "#1F2937",
                      color: "#F9FAFB"
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="alerts"
                    stroke="#F97316"
                    strokeWidth={3}
                    fill="url(#alertFill)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="grid gap-4">
            {dashboardCards.map((card) => (
              <article
                key={card.label}
                className="rounded-3xl border border-aegis-border bg-[rgba(17,24,39,0.82)] p-5 shadow-panel"
              >
                <p className="text-xs uppercase tracking-[0.35em] text-aegis-muted">
                  {card.label}
                </p>
                <p className="mt-4 text-4xl font-semibold text-aegis-text">
                  {card.value}
                </p>
                <p className="mt-3 text-sm leading-6 text-aegis-soft">
                  {card.detail}
                </p>
              </article>
            ))}
          </section>
        </main>

        <section className="grid gap-4 rounded-3xl border border-aegis-border bg-black/30 p-6 shadow-panel lg:grid-cols-3">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-aegis-muted">
              Backend
            </p>
            <h3 className="mt-3 text-lg font-semibold">API-owned integrations</h3>
            <p className="mt-2 text-sm leading-6 text-aegis-soft">
              Wazuh and Suricata integrations stay behind FastAPI service
              boundaries so the UI only consumes backend APIs.
            </p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-aegis-muted">
              Auditability
            </p>
            <h3 className="mt-3 text-lg font-semibold">Raw payload retention</h3>
            <p className="mt-2 text-sm leading-6 text-aegis-soft">
              Alert records are designed to keep normalized fields and raw
              source payloads together for investigation and debugging.
            </p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-aegis-muted">
              AI Risk Logic
            </p>
            <h3 className="mt-3 text-lg font-semibold">Scoring-ready shell</h3>
            <p className="mt-2 text-sm leading-6 text-aegis-soft">
              The monorepo includes an `ai` package so alert prioritization can
              evolve without mixing ML code into the UI or reverse proxy.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}

