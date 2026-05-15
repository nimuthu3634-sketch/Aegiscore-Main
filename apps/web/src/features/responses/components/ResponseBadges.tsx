/*
 * Response Badges reusable UI component used by the React dashboard.
 */
import { Badge } from "../../../components/ui/Badge";
import type {
  ResponseExecutionStatus,
  ResponseMode
} from "../types";

// Defines the Mode Badge Props data shape used by this frontend module.
type ModeBadgeProps = {
  mode: ResponseMode;
};

// Defines the Execution Status Badge Props data shape used by this frontend module.
type ExecutionStatusBadgeProps = {
  status: ResponseExecutionStatus;
};

const executionToneMap: Record<
  ResponseExecutionStatus,
  "success" | "warning" | "danger" | "neutral"
> = {
  succeeded: "success",
  warning: "warning",
  failed: "danger",
  pending: "neutral"
};

// Renders the Mode Badge UI section.
export function ModeBadge({ mode }: ModeBadgeProps) {
  return <Badge tone={mode === "live" ? "brand" : "outline"}>{mode}</Badge>;
}

// Renders the Execution Status Badge UI section.
export function ExecutionStatusBadge({
  status
}: ExecutionStatusBadgeProps) {
  return <Badge tone={executionToneMap[status]}>{status}</Badge>;
}
