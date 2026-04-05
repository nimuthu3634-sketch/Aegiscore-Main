import type { StatusTone } from "../../lib/theme/tokens";
import { Badge } from "./Badge";

type StatusChipProps = {
  status: StatusTone;
};

const statusToneMap: Record<
  StatusTone,
  "neutral" | "brand" | "warning" | "success" | "danger"
> = {
  new: "neutral",
  triaged: "brand",
  investigating: "warning",
  contained: "success",
  resolved: "success",
  false_positive: "neutral",
  pending_response: "warning",
  failed: "danger",
  disabled: "neutral"
};

export function StatusChip({ status }: StatusChipProps) {
  return <Badge tone={statusToneMap[status]}>{status.split("_").join(" ")}</Badge>;
}
