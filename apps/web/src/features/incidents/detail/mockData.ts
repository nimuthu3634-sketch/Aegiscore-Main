import { mockAlertsResponse } from "../../alerts/mockData";
import { mockResponsesResponse } from "../../responses/mockData";
import { mockIncidentsResponse } from "../mockData";
import type { IncidentDetailResponse } from "./types";

const alertIdsByIncident: Record<string, string[]> = {
  "INC-301": ["ALRT-1084"],
  "INC-302": ["ALRT-1086"],
  "INC-303": ["ALRT-1085"],
  "INC-304": ["ALRT-1087"],
  "INC-305": ["ALRT-1089"]
};

const incidentExtensions: Record<
  string,
  Omit<
    IncidentDetailResponse["incident"],
    keyof (typeof mockIncidentsResponse)["items"][number] | "linkedAlerts" | "relatedResponses"
  >
> = {
  "INC-301": {
    createdAt: "2026-04-05 08:15 UTC",
    updatedAt: "2026-04-05 08:41 UTC",
    primaryAssetSummary: {
      hostname: "edge-auth-01",
      ipAddress: "10.42.0.21",
      criticality: "mission_critical",
      recentAlertsCount: 6
    },
    affectedAssets: [
      {
        hostname: "edge-auth-01",
        ipAddress: "10.42.0.21",
        criticality: "mission_critical",
        recentAlertsCount: 6
      },
      {
        hostname: "vpn-gateway-01",
        ipAddress: "10.42.0.5",
        criticality: "high",
        recentAlertsCount: 2
      }
    ],
    timeline: [
      {
        id: "inc301-1",
        timestamp: "2026-04-05 08:15 UTC",
        actor: "Wazuh",
        title: "Incident opened from repeated SSH failures",
        description: "Brute-force telemetry crossed the incident creation threshold on edge-auth-01.",
        tone: "brand"
      },
      {
        id: "inc301-2",
        timestamp: "2026-04-05 08:27 UTC",
        actor: "N. Silva",
        title: "Analyst linked repeated source pattern",
        description: "Source IP overlap was confirmed against earlier auth pressure on the same asset.",
        tone: "warning"
      },
      {
        id: "inc301-3",
        timestamp: "2026-04-05 08:36 UTC",
        actor: "Response Engine",
        title: "Dry-run firewall block executed",
        description: "The model recommended a dry-run first due to potential admin access impact.",
        tone: "success"
      }
    ],
    notes: [
      {
        id: "inc-note-301",
        author: "N. Silva",
        timestamp: "2026-04-05 08:28 UTC",
        content:
          "Treat as priority while checking whether the same source touched the VPN gateway or only the SSH endpoint."
      }
    ],
    correlationExplanation:
      "This incident groups external auth-focused activity against the same edge environment and the same privileged username pattern.",
    groupedEvidence: [
      "Shared source IP against multiple authentication paths",
      "Credential-focused activity on an externally reachable asset",
      "Related dry-run response already attached to the same actor and host context"
    ],
    priorityExplanation: {
      label: "Priority explanation",
      summary:
        "The incident remains high priority because it targets an exposed authentication path and may affect privileged access.",
      rationale:
        "AegisCore keeps brute-force investigations elevated when they touch production auth infrastructure and analyst correlation confirms repeated pressure.",
      factors: [
        "Production authentication asset involved",
        "Repeated privileged-style username targeting",
        "Response preview indicates potential operational impact"
      ],
      rollupScore: 87,
      linkedAlertsCount: 1,
      scoringMethods: ["Baseline rules"]
    }
  },
  "INC-302": {
    createdAt: "2026-04-05 08:24 UTC",
    updatedAt: "2026-04-05 08:33 UTC",
    primaryAssetSummary: {
      hostname: "finance-dc-01",
      ipAddress: "10.42.11.9",
      criticality: "mission_critical",
      recentAlertsCount: 3
    },
    affectedAssets: [
      {
        hostname: "finance-dc-01",
        ipAddress: "10.42.11.9",
        criticality: "mission_critical",
        recentAlertsCount: 3
      }
    ],
    timeline: [
      {
        id: "inc302-1",
        timestamp: "2026-04-05 08:24 UTC",
        actor: "Wazuh",
        title: "Incident created from privileged account creation",
        description: "Unauthorized user creation rule matched on the finance domain controller.",
        tone: "danger"
      },
      {
        id: "inc302-2",
        timestamp: "2026-04-05 08:30 UTC",
        actor: "R. Perera",
        title: "Analyst confirmed no approved change window",
        description: "The new account could not be matched to planned admin activity.",
        tone: "warning"
      },
      {
        id: "inc302-3",
        timestamp: "2026-04-05 08:33 UTC",
        actor: "Response Engine",
        title: "Account disable response succeeded",
        description: "A linked response disabled the account after analyst approval.",
        tone: "success"
      }
    ],
    notes: [
      {
        id: "inc-note-302",
        author: "R. Perera",
        timestamp: "2026-04-05 08:31 UTC",
        content:
          "Directory review indicates the new account was added to privileged groups immediately after creation."
      }
    ],
    correlationExplanation:
      "The incident is grouped around a single privileged identity event on a business-critical directory asset with immediate admin-group assignment.",
    groupedEvidence: [
      "Privileged account created on finance domain controller",
      "Group membership suggests escalated access intent",
      "Live disable response succeeded and is linked to the same incident"
    ],
    priorityExplanation: {
      label: "Priority explanation",
      summary:
        "Critical priority is justified by the identity-sensitive asset, privileged account scope, and confirmed lack of change approval.",
      rationale:
        "Identity manipulation on core directory services receives the highest operational priority in the current SME-safe model.",
      factors: [
        "Mission-critical directory asset involved",
        "Privileged role assignment detected",
        "Analyst validation removed benign explanation path"
      ],
      rollupScore: 95,
      linkedAlertsCount: 1,
      scoringMethods: ["Baseline rules"]
    }
  },
  "INC-303": {
    createdAt: "2026-04-05 08:18 UTC",
    updatedAt: "2026-04-05 08:20 UTC",
    primaryAssetSummary: {
      hostname: "branch-fw-02",
      ipAddress: "172.16.4.8",
      criticality: "high",
      recentAlertsCount: 9
    },
    affectedAssets: [
      {
        hostname: "branch-fw-02",
        ipAddress: "172.16.4.8",
        criticality: "high",
        recentAlertsCount: 9
      }
    ],
    timeline: [
      {
        id: "inc303-1",
        timestamp: "2026-04-05 08:18 UTC",
        actor: "Suricata",
        title: "Port scan activity grouped into new incident",
        description: "Network telemetry matched the port-scan correlation rules for the branch firewall.",
        tone: "brand"
      }
    ],
    notes: [],
    correlationExplanation:
      "This incident groups scanning behavior observed against a single branch firewall asset from one internal source range.",
    groupedEvidence: [
      "Single source range probing remote-access ports",
      "No linked credential or integrity signals yet"
    ],
    priorityExplanation: {
      label: "Priority explanation",
      summary:
        "Medium priority reflects broad scan coverage with limited follow-on evidence.",
      rationale:
        "The incident stays visible but below high until corroborating compromise indicators appear.",
      factors: [
        "Important network edge asset involved",
        "Single source range and limited blast evidence"
      ],
      rollupScore: 61,
      linkedAlertsCount: 1,
      scoringMethods: ["Baseline rules"]
    }
  },
  "INC-304": {
    createdAt: "2026-04-05 08:32 UTC",
    updatedAt: "2026-04-05 08:57 UTC",
    primaryAssetSummary: {
      hostname: "ops-files-03",
      ipAddress: "10.42.7.54",
      criticality: "high",
      recentAlertsCount: 4
    },
    affectedAssets: [
      {
        hostname: "ops-files-03",
        ipAddress: "10.42.7.54",
        criticality: "high",
        recentAlertsCount: 4
      }
    ],
    timeline: [
      {
        id: "inc304-1",
        timestamp: "2026-04-05 08:32 UTC",
        actor: "Wazuh",
        title: "Critical file-integrity change escalated",
        description: "Sensitive file-share changes crossed the incident threshold.",
        tone: "warning"
      },
      {
        id: "inc304-2",
        timestamp: "2026-04-05 08:50 UTC",
        actor: "Response Engine",
        title: "Host isolation succeeded",
        description: "The related response action contained the affected file server.",
        tone: "success"
      }
    ],
    notes: [
      {
        id: "inc-note-304",
        author: "J. Fernando",
        timestamp: "2026-04-05 08:58 UTC",
        content:
          "Hash evidence captured and the affected workbook preserved for offline comparison."
      }
    ],
    correlationExplanation:
      "The incident centers on sensitive file changes on one operations file host with immediate containment.",
    groupedEvidence: [
      "File-integrity alert on protected operations share",
      "Successful isolation response attached"
    ],
    priorityExplanation: {
      label: "Priority explanation",
      summary:
        "Priority remains high because integrity changes on business-critical files often precede broader operational risk.",
      rationale:
        "Containment reduced urgency, but the evidence still warrants a high-priority investigation path.",
      factors: [
        "Sensitive operational files impacted",
        "Containment executed after confirmation"
      ],
      rollupScore: 79,
      linkedAlertsCount: 1,
      scoringMethods: ["Baseline rules"]
    }
  },
  "INC-305": {
    createdAt: "2026-04-05 07:40 UTC",
    updatedAt: "2026-04-05 07:58 UTC",
    primaryAssetSummary: {
      hostname: "warehouse-edge-02",
      ipAddress: "172.21.8.22",
      criticality: "standard",
      recentAlertsCount: 1
    },
    affectedAssets: [
      {
        hostname: "warehouse-edge-02",
        ipAddress: "172.21.8.22",
        criticality: "standard",
        recentAlertsCount: 1
      }
    ],
    timeline: [
      {
        id: "inc305-1",
        timestamp: "2026-04-05 07:40 UTC",
        actor: "Suricata",
        title: "Low-noise scan grouped for review",
        description: "A small port-scan pattern was bundled for analyst review.",
        tone: "brand"
      },
      {
        id: "inc305-2",
        timestamp: "2026-04-05 07:58 UTC",
        actor: "SOC Queue",
        title: "Incident resolved as tuning candidate",
        description: "No supporting compromise signal found after review.",
        tone: "success"
      }
    ],
    notes: [],
    correlationExplanation:
      "This incident collects low-confidence port-scan activity that was closed after confirming a benign tuning issue.",
    groupedEvidence: [
      "Low-confidence sensor signature",
      "No corroborating alert families or response need"
    ],
    priorityExplanation: {
      label: "Priority explanation",
      summary:
        "Low priority is appropriate because the case was resolved as a tuning issue without additional evidence.",
      rationale:
        "The model discounts already-resolved cases lacking corroborating behavior.",
      factors: [
        "No follow-on evidence",
        "Resolution path already completed"
      ],
      rollupScore: 34,
      linkedAlertsCount: 1,
      scoringMethods: ["Baseline rules"]
    }
  }
};

export const mockIncidentDetailsById = Object.fromEntries(
  mockIncidentsResponse.items.map((incident) => {
    const linkedAlertIds = alertIdsByIncident[incident.id] ?? [];

    const linkedAlerts = mockAlertsResponse.items
      .filter((alert) => linkedAlertIds.includes(alert.id))
      .map((alert) => ({
        id: alert.id,
        detectionType: alert.detectionType,
        sourceType: alert.sourceType,
        severity: alert.severity,
        status: alert.status,
        asset: alert.asset,
        sourceIp: alert.sourceIp,
        timestamp: alert.timestamp,
        riskScore: alert.riskScore,
        eventId: alert.eventId
      }));

    const relatedResponses = mockResponsesResponse.items
      .filter((response) => response.linkedEntity === incident.id)
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
      }));

    return [
      incident.id,
      {
        incident: {
          ...incident,
          ...incidentExtensions[incident.id],
          linkedAlerts,
          relatedResponses
        },
        fetchedAt: mockIncidentsResponse.generatedAt
      }
    ];
  })
) as Record<string, IncidentDetailResponse>;
