/**
 * Copy and helpers for the final AI/ML product story:
 * Wazuh/Suricata detect; TensorFlow prioritizes (Low/Medium/High only);
 * built-in IP block may apply only to brute_force under strict gates.
 */

export type AiPriorityTier = "low" | "medium" | "high";

const ML_BRUTE_RULE = "ml_brute_force_auto_block_v1";

export function isTensorFlowScoringMethod(value: string | null | undefined): boolean {
  return (value ?? "").toLowerCase() === "tensorflow_model";
}

export function normalizeAiTier(raw: string | null | undefined): AiPriorityTier | null {
  if (!raw) {
    return null;
  }
  const key = raw.trim().toLowerCase();
  if (key === "low" || key === "medium" || key === "high") {
    return key;
  }
  return null;
}

export function formatAiTierTitleCase(tier: AiPriorityTier): "Low" | "Medium" | "High" {
  return tier === "low" ? "Low" : tier === "medium" ? "Medium" : "High";
}

export function formatClassProbabilitiesLine(
  probs: Record<string, number> | null | undefined
): string | null {
  if (!probs || typeof probs !== "object") {
    return null;
  }
  const order: AiPriorityTier[] = ["low", "medium", "high"];
  const parts: string[] = [];
  for (const key of order) {
    const v = probs[key];
    if (typeof v === "number" && Number.isFinite(v)) {
      parts.push(`${formatAiTierTitleCase(key)} ${Math.round(v * 100)}%`);
    }
  }
  return parts.length ? parts.join(" · ") : null;
}

export function summarizeMlBruteForceBlock(details: Record<string, unknown> | undefined): string | null {
  if (!details || typeof details !== "object") {
    return null;
  }
  if (details.automation_rule !== ML_BRUTE_RULE) {
    return null;
  }
  const evaluation = details.ml_brute_force_evaluation;
  if (!evaluation || typeof evaluation !== "object") {
    return "Built-in automated IP block for brute_force (TensorFlow High tier and login-density gates).";
  }
  const ev = evaluation as Record<string, unknown>;
  const checks = (ev.checks ?? {}) as Record<string, unknown>;
  const thresholds = (ev.thresholds ?? {}) as Record<string, unknown>;
  const ip = (typeof ev.resolved_source_ip === "string" && ev.resolved_source_ip.trim()
    ? ev.resolved_source_ip
    : typeof details.target === "string"
      ? details.target
      : null) as string | null;
  const required = thresholds.required_failed_logins_5m;
  const failed = checks.failed_logins_5m;
  const parts: string[] = [];
  if (ip) {
    parts.push(`Source IP ${ip} was blocked by the built-in ML brute-force automation.`);
  } else {
    parts.push("An IP was blocked by the built-in ML brute-force automation.");
  }
  parts.push(
    `Conditions: TensorFlow prioritization High, failed logins (5m) ≥ ${typeof required === "number" ? required : 10} (observed: ${typeof failed === "number" ? failed : "n/a"}), and a resolvable attacker IP.`
  );
  parts.push("Other detection types never use this built-in auto-block path.");
  return parts.join(" ");
}

export const AUTOMATED_BLOCK_SCOPE_NOTE =
  "Built-in automated IP blocking applies only to brute_force alerts when TensorFlow prioritization is High and login-density gates pass. Port scan, file integrity, and unauthorized user creation are never auto-blocked by this rule.";
