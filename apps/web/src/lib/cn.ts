/*
 * Frontend helper utilities shared across the React application.
 */
export function cn(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(" ");
}
