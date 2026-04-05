export function formatTokenLabel(value: string | null | undefined) {
  if (!value) {
    return "n/a";
  }

  return value
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase())
    .replace(/\bIp\b/g, "IP")
    .replace(/\bId\b/g, "ID")
    .replace(/\bSoc\b/g, "SOC");
}

export function formatScoreMethodLabel(value: string | null | undefined) {
  switch (value) {
    case "baseline_rules":
      return "Baseline rules";
    case "sklearn_model":
      return "Scikit-learn model";
    default:
      return formatTokenLabel(value);
  }
}

export function formatDriverLabel(driver: {
  label?: unknown;
  contribution?: unknown;
  feature?: unknown;
}) {
  const label =
    typeof driver.label === "string" && driver.label.trim()
      ? driver.label.trim()
      : typeof driver.feature === "string" && driver.feature.trim()
        ? formatTokenLabel(driver.feature)
        : "Scoring driver";
  const contribution =
    typeof driver.contribution === "number"
      ? driver.contribution
      : typeof driver.contribution === "string"
        ? Number(driver.contribution)
        : null;

  if (Number.isFinite(contribution)) {
    return `+${contribution} ${label}`;
  }

  return label;
}
