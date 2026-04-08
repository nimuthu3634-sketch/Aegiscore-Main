import { formatTokenLabel } from "./formatters";

/**
 * Canonical four supported AegisCore detection types (aligned with backend `DetectionType`).
 * UI filters and reports should derive options from this list so all scenarios stay first-class.
 */
export const SUPPORTED_DETECTION_TYPES = [
  "brute_force",
  "file_integrity_violation",
  "port_scan",
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
