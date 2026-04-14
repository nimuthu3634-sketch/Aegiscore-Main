import { formatTokenLabel } from "./formatters";

/** Standard product copy for panels, login, and examiner-facing UI (aligned with documentation). */
export const ACADEMIC_THREAT_SCOPE_DESCRIPTION =
  "AegisCore validates four core threat categories: brute-force attacks, port scans, file integrity violations, and unauthorized user account creation.";

/** Short roadmap disclaimer—broader categories are not implemented in this release. */
export const ACADEMIC_THREAT_SCOPE_ROADMAP_NOTE =
  "Additional detection categories are future roadmap items, not part of the current implementation.";

/**
 * Canonical four supported AegisCore detection types (aligned with backend `DetectionType`
 * iteration order: brute_force → port_scan → file_integrity_violation → unauthorized_user_creation).
 */
export const SUPPORTED_DETECTION_TYPES = [
  "brute_force",
  "port_scan",
  "file_integrity_violation",
  "unauthorized_user_creation"
] as const;

export type SupportedDetectionType = (typeof SUPPORTED_DETECTION_TYPES)[number];

export function supportedDetectionSelectOptions(): Array<{
  value: string;
  label: string;
}> {
  return SUPPORTED_DETECTION_TYPES.map((value) => ({
    value,
    label: formatTokenLabel(value)
  }));
}