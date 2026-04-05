import { mockResponsesResponse } from "../../responses/mockData";
import { mockAlertsResponse } from "../mockData";
import type { AlertDetailResponse } from "./types";

const linkedIncidentByAlertId: Record<string, string | null> = {
  "ALRT-1084": "INC-301",
  "ALRT-1085": "INC-303",
  "ALRT-1086": "INC-302",
  "ALRT-1087": "INC-304",
  "ALRT-1088": null,
  "ALRT-1089": "INC-305"
};

const detailExtensions: Record<
  string,
  Omit<
    AlertDetailResponse["alert"],
    keyof (typeof mockAlertsResponse)["items"][number] | "linkedIncidentId" | "relatedResponses"
  >
> = {
  "ALRT-1084": {
    destinationIp: "10.42.0.21",
    ruleId: "100210",
    sourceRule: "sshd.auth.failures",
    normalizedSummary:
      "A sequence of repeated failed SSH authentications matched the brute-force detection profile for edge-auth-01.",
    normalizedDetails: [
      { label: "Alert ID", value: "ALRT-1084", mono: true },
      { label: "Detection", value: "brute_force", mono: true },
      { label: "Source type", value: "Wazuh", emphasized: true },
      { label: "Username", value: "svc-admin", mono: true },
      { label: "Source IP", value: "185.244.25.11", mono: true },
      { label: "Destination IP", value: "10.42.0.21", mono: true }
    ],
    rawPayload: {
      manager: { name: "wazuh-manager-01" },
      rule: { id: 100210, description: "Multiple failed SSH login attempts" },
      agent: { id: "005", name: "edge-auth-01", ip: "10.42.0.21" },
      data: {
        srcip: "185.244.25.11",
        dstip: "10.42.0.21",
        dstport: "22",
        username: "svc-admin",
        event_id: "evt-54fd8c"
      }
    },
    scoreExplanation: {
      score: 87,
      label: "Alert risk explanation",
      summary:
        "This alert scores high because an exposed authentication endpoint was targeted repeatedly with account-focused activity.",
      rationale:
        "AegisCore raises the score when the same source repeatedly targets privileged usernames on a production-facing auth asset.",
      factors: [
        "Repeated failed authentication pattern on an internet-facing asset",
        "Privileged-style username present in the event stream",
        "SSH destination port aligned to sensitive access path",
        "Linked incident already open for the same host and source pattern"
      ],
      drivers: ["Repeated failed logins", "Privileged account flag", "Sensitive access path"]
    },
    notes: [
      {
        id: "alert-note-1",
        author: "N. Silva",
        timestamp: "2026-04-05 08:27 UTC",
        content:
          "Source IP overlaps with earlier failed-auth spikes on the same edge host. Keep linked to the current incident."
      }
    ]
  },
  "ALRT-1085": {
    destinationIp: "172.16.4.8",
    ruleId: "SURI-PT-9",
    sourceRule: "suricata.port-scan",
    normalizedSummary:
      "The network sensor observed broad destination port coverage against the branch firewall from an internal scanning origin.",
    normalizedDetails: [
      { label: "Alert ID", value: "ALRT-1085", mono: true },
      { label: "Detection", value: "port_scan", mono: true },
      { label: "Source type", value: "Suricata", emphasized: true },
      { label: "Source IP", value: "10.88.4.51", mono: true },
      { label: "Destination IP", value: "172.16.4.8", mono: true },
      { label: "Destination port", value: "3389", mono: true }
    ],
    rawPayload: {
      sensor: "suricata-branch-02",
      signature_id: "SURI-PT-9",
      event_type: "alert",
      src_ip: "10.88.4.51",
      dest_ip: "172.16.4.8",
      dest_port: 3389,
      flow_id: "4728190021"
    },
    scoreExplanation: {
      score: 61,
      label: "Alert risk explanation",
      summary:
        "This alert remains medium because the target is important, but the scan source is still inside a monitored network range.",
      rationale:
        "The model lowers the score slightly when the source IP belongs to a known network segment and there is no follow-on compromise indicator.",
      factors: [
        "Multi-port probing behavior confirmed by network telemetry",
        "Source IP currently maps to an internal branch range",
        "No credential or file-integrity signal linked yet"
      ],
      drivers: ["Time-window density", "Repeated source IP", "Detection type: port scan"]
    },
    notes: [
      {
        id: "alert-note-2",
        author: "SOC Queue",
        timestamp: "2026-04-05 08:22 UTC",
        content:
          "Branch asset owner should confirm whether the source host belongs to vulnerability scanning or an unknown workstation."
      }
    ]
  },
  "ALRT-1086": {
    destinationIp: "10.42.11.9",
    ruleId: "110884",
    sourceRule: "windows.account.create",
    normalizedSummary:
      "A new administrative-style account appeared on the finance domain controller outside approved change timing.",
    normalizedDetails: [
      { label: "Alert ID", value: "ALRT-1086", mono: true },
      { label: "Detection", value: "unauthorized_user_creation", mono: true },
      { label: "Source type", value: "Wazuh", emphasized: true },
      { label: "Username", value: "unknown-admin", mono: true },
      { label: "Source IP", value: "10.42.11.9", mono: true },
      { label: "Destination port", value: "389", mono: true }
    ],
    rawPayload: {
      manager: { name: "wazuh-manager-01" },
      rule: { id: 110884, description: "Unexpected user creation event" },
      agent: { id: "021", name: "finance-dc-01", ip: "10.42.11.9" },
      data: {
        username: "unknown-admin",
        group: "Domain Admins",
        process: "lsass.exe",
        source_rule: "windows.account.create",
        event_id: "evt-a190d2"
      }
    },
    scoreExplanation: {
      score: 95,
      label: "Alert risk explanation",
      summary:
        "This alert scores critical because it indicates privileged account creation on a mission-critical domain controller.",
      rationale:
        "Privileged account lifecycle changes on directory infrastructure receive the highest weighting in the current SME-safe scoring logic.",
      factors: [
        "Privileged account creation on finance domain controller",
        "Business-critical infrastructure involved",
        "Pending response already attached",
        "No approved maintenance window matched the event"
      ],
      drivers: ["Privileged account flag", "Asset criticality", "Unauthorized user creation"]
    },
    notes: [
      {
        id: "alert-note-3",
        author: "R. Perera",
        timestamp: "2026-04-05 08:30 UTC",
        content:
          "Analyst confirmed no related approved admin onboarding request. Keep linked to INC-302 and review directory logs."
      }
    ]
  },
  "ALRT-1087": {
    destinationIp: "10.42.7.54",
    ruleId: "100988",
    sourceRule: "fim.critical.file.change",
    normalizedSummary:
      "Unexpected file integrity change detected on an operations share after hours, followed by immediate containment.",
    normalizedDetails: [
      { label: "Alert ID", value: "ALRT-1087", mono: true },
      { label: "Detection", value: "file_integrity_violation", mono: true },
      { label: "Source type", value: "Wazuh", emphasized: true },
      { label: "Asset", value: "ops-files-03", emphasized: true },
      { label: "Source IP", value: "10.42.7.54", mono: true },
      { label: "Destination port", value: "445", mono: true }
    ],
    rawPayload: {
      manager: { name: "wazuh-manager-01" },
      rule: { id: 100988, description: "Critical file change detected" },
      agent: { id: "014", name: "ops-files-03", ip: "10.42.7.54" },
      file: {
        path: "D:\\Operations\\Policies\\access-control.xlsx",
        hash_after: "9aa4cb322f7810ba6a6301f39f00409d"
      },
      event_id: "evt-c8ae24"
    },
    scoreExplanation: {
      score: 79,
      label: "Alert risk explanation",
      summary:
        "The score stays high because the affected file path is sensitive, but containment already reduced immediate exposure.",
      rationale:
        "The current model lowers the final score once a related incident is already contained by policy or analyst action.",
      factors: [
        "Sensitive file-share content changed unexpectedly",
        "After-hours timing increased confidence",
        "Containment action already executed successfully"
      ],
      drivers: ["Sensitive file flag", "Response history", "After-hours activity"]
    },
    notes: [
      {
        id: "alert-note-4",
        author: "J. Fernando",
        timestamp: "2026-04-05 08:58 UTC",
        content:
          "Asset isolated and file hash preserved for follow-up review in the incident timeline."
      }
    ]
  },
  "ALRT-1088": {
    destinationIp: "10.42.0.5",
    ruleId: "SURI-BF-2",
    sourceRule: "suricata.auth.burst",
    normalizedSummary:
      "VPN authentication bursts matched the brute-force heuristic on the gateway service.",
    normalizedDetails: [
      { label: "Alert ID", value: "ALRT-1088", mono: true },
      { label: "Detection", value: "brute_force", mono: true },
      { label: "Source type", value: "Suricata", emphasized: true },
      { label: "Source IP", value: "202.129.41.77", mono: true },
      { label: "Destination IP", value: "10.42.0.5", mono: true },
      { label: "Destination port", value: "443", mono: true }
    ],
    rawPayload: {
      sensor: "suricata-edge-01",
      signature_id: "SURI-BF-2",
      src_ip: "202.129.41.77",
      dest_ip: "10.42.0.5",
      dest_port: 443,
      username: "vpn-auth",
      event_id: "evt-c42f8d"
    },
    scoreExplanation: {
      score: 68,
      label: "Alert risk explanation",
      summary:
        "The score remains medium-high due to external sourcing but no confirmed identity compromise yet.",
      rationale:
        "The event is strong enough to stay visible, but the model holds it below critical until follow-on success or privilege indicators appear.",
      factors: [
        "External source targeting authentication service",
        "Gateway asset has elevated operational sensitivity",
        "No linked incident or response history yet"
      ],
      drivers: ["External source IP", "Asset criticality", "Detection type: brute force"]
    },
    notes: []
  },
  "ALRT-1089": {
    destinationIp: "172.21.8.22",
    ruleId: "SURI-PT-3",
    sourceRule: "suricata.port-scan.low-noise",
    normalizedSummary:
      "A lower-confidence scan pattern was recorded and later closed after tuning review.",
    normalizedDetails: [
      { label: "Alert ID", value: "ALRT-1089", mono: true },
      { label: "Detection", value: "port_scan", mono: true },
      { label: "Source type", value: "Suricata", emphasized: true },
      { label: "Source IP", value: "172.21.8.22", mono: true },
      { label: "Destination IP", value: "172.21.8.22", mono: true },
      { label: "Destination port", value: "n/a", mono: true }
    ],
    rawPayload: {
      sensor: "suricata-warehouse-01",
      signature_id: "SURI-PT-3",
      src_ip: "172.21.8.22",
      dest_ip: "172.21.8.22",
      event_id: "evt-f34dd1"
    },
    scoreExplanation: {
      score: 34,
      label: "Alert risk explanation",
      summary:
        "This alert stays low because it was resolved through tuning and there is no corroborating compromise signal.",
      rationale:
        "The risk model discounts alerts once the related activity is closed as noise and supporting evidence is absent.",
      factors: [
        "Low-confidence scan signature",
        "No matching compromise or persistence indicators",
        "Closed after sensor-tuning review"
      ],
      drivers: ["Low-confidence signature", "No recurrence history", "Resolved status"]
    },
    notes: []
  }
};

export const mockAlertDetailsById: Record<string, AlertDetailResponse> =
  Object.fromEntries(
    mockAlertsResponse.items.map((alert) => [
      alert.id,
      {
        fetchedAt: "2026-04-05T09:10:00Z",
        alert: {
          ...alert,
          linkedIncidentId: linkedIncidentByAlertId[alert.id] ?? null,
          relatedResponses: mockResponsesResponse.items
            .filter((response) => response.linkedEntity === alert.id)
            .map((response) => ({
              id: response.id,
              actionType: response.actionType,
              policyName: response.policyName,
              target: response.target,
              mode: response.mode,
              executionStatus: response.executionStatus,
              executedAt: response.executedAt,
              resultSummary: response.resultSummary,
              resultMessage: response.resultMessage,
              attemptCount: response.attemptCount
            })),
          ...detailExtensions[alert.id]
        }
      }
    ])
  );
