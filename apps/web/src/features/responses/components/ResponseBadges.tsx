import { Badge } from "../../../components/ui/Badge";
import type {
  ResponseExecutionStatus,
  ResponseMode
} from "../types";

type ModeBadgeProps = {
  mode: ResponseMode;
};

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

export function ModeBadge({ mode }: ModeBadgeProps) {
  return <Badge tone={mode === "live" ? "brand" : "outline"}>{mode}</Badge>;
}

export function ExecutionStatusBadge({
  status
}: ExecutionStatusBadgeProps) {
  return <Badge tone={executionToneMap[status]}>{status}</Badge>;
}
