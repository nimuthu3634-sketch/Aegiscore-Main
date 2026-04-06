# AegisCore Frontend Component Inventory

## Purpose

This document converts the confirmed Figma page blueprint into an implementation-oriented component inventory. It is intended to be used alongside the design spec in [docs/frontend/aegiscore-design-spec.md](/C:/Users/nimus/OneDrive/Documents/GitHub/Aegiscore-Main/docs/frontend/aegiscore-design-spec.md).

Confirmed future Figma mapping anchors:

- `01 Design System` -> `1:2`
- `02 Wireframes` -> `1:3`
- `03 High-Fidelity Screens` -> `1:4`

## 1. Design Tokens

### Color Tokens

- `color.brand.primary`
- `color.brand.primaryHover`
- `color.brand.ink`
- `color.brand.divider`
- `color.brand.glow`
- `color.bg.base`
- `color.bg.panel`
- `color.border.default`
- `color.text.primary`
- `color.text.secondary`
- `color.text.muted`
- `color.state.danger`
- `color.state.success`
- `color.state.warning`
- `color.surface.panelRaised`
- `color.surface.panelSubtle`
- `color.surface.overlay`
- `color.surface.accentSoft`
- `color.surface.successSoft`
- `color.surface.warningSoft`
- `color.surface.dangerSoft`

### Typography Tokens

- `type.display.lg`
- `type.display.md`
- `type.heading.lg`
- `type.heading.md`
- `type.heading.sm`
- `type.body.md`
- `type.body.sm`
- `type.label.md`
- `type.label.sm`
- `type.mono.md`
- `type.mono.sm`

### Spatial Tokens

- Spacing: `space.0`, `space.1`, `space.2`, `space.3`, `space.4`, `space.5`, `space.6`, `space.8`, `space.10`, `space.12`, `space.16`
- Radius: `radius.none`, `radius.sm`, `radius.md`, `radius.lg`, `radius.xl`, `radius.full`
- Shadow: `shadow.panel`, `shadow.float`, `shadow.modal`, `shadow.focus`

## 2. Layout Primitives

| Primitive | Role | Default Behavior | Primary Pages |
| --- | --- | --- | --- |
| `AuthShell` | Split login layout | Branded background plus centered auth card | Login |
| `AppShell` | Main app frame | Sidebar + top nav + content area | All authenticated pages |
| `SidebarNav` | Primary navigation scaffold | Fixed desktop rail, drawer or collapsed tablet state | All authenticated pages |
| `TopNav` | Global utility bar | Page title, search, health, user menu | All authenticated pages |
| `PageContainer` | Page wrapper | Standard max width, consistent padding, vertical section spacing | All pages |
| `PageHeader` | Page intro and controls | Title, subtitle, actions, status context | All pages |
| `MetricGrid` | KPI card grid | 2 to 4 cards with equal heights | Dashboard, Reports, Response History |
| `PanelCard` | Core bordered surface | Standard content card with title and body slots | Most pages |
| `SplitPanel` | Main-detail layout | Flexible two-column layout with fixed-width aside | Detail pages, Rules, Assets |
| `ToolbarRow` | Filters and actions | Dense horizontal control row above table or chart | Alerts, Incidents, Assets, Responses |
| `SectionStack` | Vertical content grouping | Reusable spacing wrapper for cards and sections | All pages |
| `DetailTabs` | Investigation section navigation | Sticky or in-flow segmented tabs | Alert / Incident Detail |
| `TimelineRail` | Chronological event stream | Ordered event list with timestamps and chips | Detail, Response History |
| `ModalLayout` | Dialog structure | Header, content, footer with fixed action zones | Modals |
| `StateBlock` | Empty, loading, error surface | Consistent state presentation block | All pages |

## 3. Reusable Components

### Branding And Navigation

| Component | Role | Key Variants | Primary Pages |
| --- | --- | --- | --- |
| `AegisCoreLogoLockup` | Brand identity | full, compact, icon-only | Login, Sidebar, TopNav, Reports |
| `NavItem` | Sidebar row | default, hover, active, badge-count | All authenticated pages |
| `NavSectionLabel` | Sidebar grouping label | default | Sidebar |
| `EnvironmentPill` | Tenant or environment context | default, warning | Sidebar, Login, TopNav |
| `GlobalSearch` | Quick search field | idle, focused, loading | TopNav |
| `HealthIndicator` | API or integration health | healthy, degraded, down | TopNav, Login |
| `UserMenuTrigger` | Session entry point | default, open | TopNav |

### Actions And Inputs

| Component | Role | Key Variants | Primary Pages |
| --- | --- | --- | --- |
| `Button` | Primary action control | primary, secondary, ghost, danger, icon-only | All pages |
| `SearchInput` | Filtered search | default, with prefix icon | Alerts, Incidents, Assets |
| `TextInput` | General input | default, error, disabled, read-only | Login, Settings, Rules |
| `PasswordInput` | Auth input | default, reveal toggle | Login |
| `SelectInput` | Single selection | default, error, disabled | Filters, Settings |
| `MultiSelectInput` | Multi-value filters | default, compact | Alerts, Reports |
| `TextArea` | Notes and policy descriptions | default, error | Detail, Rules, Settings |
| `ToggleSwitch` | Enable or disable setting | off, on, disabled | Rules, Settings |
| `SegmentedControl` | Dense local mode switch | default, active | Dashboard, Settings, Reports |
| `FilterChip` | Active filter token | default, removable | Alerts, Incidents, Assets |

### Status And Metadata

| Component | Role | Key Variants | Primary Pages |
| --- | --- | --- | --- |
| `SourceBadge` | Alert source marker | Wazuh, Suricata | Alerts, Detail, Incidents |
| `DetectionBadge` | Detection identifier | brute_force, file_integrity_violation, port_scan, unauthorized_user_creation | Alerts, Detail, Rules |
| `SeverityChip` | Severity indicator | critical, high, medium, low | Alerts, Detail, Incidents |
| `StatusChip` | Workflow state indicator | new, triaged, investigating, contained, resolved, failed, disabled | All operational pages |
| `RiskScoreChip` | Scored risk summary | low, medium, high with numeric value | Alerts, Detail, Dashboard |
| `ActorBadge` | Human or automation actor marker | analyst, admin, automation | Response History, Audit |
| `EnvironmentBadge` | Asset grouping | production, office, remote | Assets, Detail |
| `TimestampMeta` | Time display | absolute, absolute-plus-relative | Tables, Timeline, Detail |

### Data Display

| Component | Role | Key Variants | Primary Pages |
| --- | --- | --- | --- |
| `MetricCard` | KPI summary | neutral, highlight, warning, danger | Dashboard, Response History, Assets |
| `DataTable` | Dense tabular display | default, selectable, compact | Alerts, Incidents, Assets, Responses |
| `TableHeaderCell` | Sortable header | default, sorted-asc, sorted-desc | Data tables |
| `TableRowActionMenu` | Overflow row actions | closed, open | Tables |
| `KeyValueList` | Technical metadata layout | default, compact | Detail, Settings |
| `EvidenceList` | Evidence group renderer | default, collapsible | Alert / Incident Detail |
| `TimelineEvent` | Timeline row | neutral, warning, danger, success | Detail, Response History |
| `RawPayloadViewer` | Raw JSON or payload viewer | collapsed, expanded | Detail |
| `AuditTrailList` | Change history list | default | Detail, Settings |

### Charts And Visual Summaries

| Component | Role | Key Variants | Primary Pages |
| --- | --- | --- | --- |
| `ChartCard` | Chart wrapper surface | default, compact | Dashboard, Reports |
| `AlertVolumeChart` | Trend chart | 24h, 7d, 30d | Dashboard, Reports |
| `SeverityDistributionChart` | Severity mix chart | by-source, by-detection | Dashboard, Reports |
| `IncidentStatusChart` | Incident state distribution | current snapshot | Dashboard, Reports |
| `SparklineMetric` | Mini trend summary | up, down, flat | KPI cards |

### Feedback And Workflow

| Component | Role | Key Variants | Primary Pages |
| --- | --- | --- | --- |
| `EmptyStateCard` | No-data state | no-alerts, no-incidents, no-reports | All pages |
| `LoadingSkeleton` | Loading placeholder | card, table, detail, chart | All pages |
| `ErrorPanel` | Inline failure surface | retryable, terminal | All pages |
| `ConfirmActionModal` | Response confirmation | safe, destructive | Detail, Responses, Rules |
| `FormModal` | Edit flow modal | medium, large | Rules, Reports, Settings |
| `ToastNotice` | Lightweight completion state | success, warning, error | Global |

## 4. Page-Level Sections

### Login

- Brand panel
- Auth card
- Environment context
- Support or status note

### Overview Dashboard

- Page header
- KPI row
- Alert volume chart section
- Severity or source chart section
- Incident queue snapshot
- Response history snapshot
- High-risk assets section
- AI or risk insight card

### Alerts

- Page header
- Filter toolbar
- Active filters strip
- Alerts table
- Optional alert preview panel

### Alert / Incident Detail

- Detail header
- Summary card
- Risk score card
- Asset context card
- Investigation timeline
- Evidence section
- Response actions section
- Raw payload viewer
- Audit history

### Incidents Queue

- Header with queue counts
- Filter toolbar
- Incidents table
- Selected incident snapshot panel

### Assets / Endpoints

- Header with asset metrics
- Filter toolbar
- Assets table
- Asset detail panel
- Related alerts snapshot

### Response History

- Header with response metrics
- Filter toolbar
- Response history table
- Optional timeline or grouped history view

### Rules / Policies

- Page header with scope reminder
- Rules list
- Policy detail panel
- Edit form modal

### Reports

- Page header
- Report template cards or table
- Generate report panel
- Recent reports history

### Settings

- Settings navigation
- Section cards for integrations, auth, notifications, retention, audit
- Save and validation actions

## 5. Data Visualization Components

Use Recharts for the first implementation pass. Chart wrappers should hide raw library configuration behind reusable components.

| Component | Data Shape | Key Notes |
| --- | --- | --- |
| `AlertVolumeChart` | `[{ timestamp, count }]` | Area or line chart with orange primary trend |
| `SeverityDistributionChart` | `[{ label, critical, high, medium, low }]` | Stacked bars preferred over pie-heavy summaries |
| `IncidentStatusChart` | `[{ status, count }]` | Horizontal bar or compact donut only if count of statuses stays small |
| `SparklineMetric` | `[{ timestamp, value }]` | Lightweight KPI trend line |
| `ResponseOutcomeChart` | `[{ outcome, count }]` | Success, warning, danger states only |
| `AssetExposureChart` | `[{ assetGroup, count }]` | Use in reports or dashboard side card |

Chart implementation rules:

- Every chart should sit inside a `ChartCard`.
- Tooltips must inherit AegisCore panel styling.
- Legends should be minimal and use readable labels, not color alone.
- The first chart pass should prioritize readability over animation complexity.

## 6. Future Figma Mapping Notes

These notes keep the repo docs aligned with the confirmed Figma pages until direct canvas editing is available.

### `01 Design System` -> `1:2`

Create future sections and frames in this order:

1. `Color Palette`
2. `Typography`
3. `Spacing Scale`
4. `Buttons`
5. `Inputs`
6. `Badges`
7. `Severity Chips`
8. `Status Chips`
9. `Tables`
10. `Cards`
11. `Sidebar`
12. `Top Navigation`
13. `Charts`
14. `Modals`
15. `Empty States`

Recommended frame naming convention:

- `Buttons / Primary / Default`
- `Buttons / Secondary / Hover`
- `Inputs / Text / Default`
- `Tables / Alerts / Desktop`
- `Charts / Alert Volume / Default`

### `02 Wireframes` -> `1:3`

Create low-fidelity frames with these names:

- `Login / Desktop`
- `Overview Dashboard / Desktop`
- `Alerts / Desktop`
- `Alert Detail / Desktop`
- `Incidents Queue / Desktop`
- `Assets / Desktop`
- `Response History / Desktop`
- `Rules Policies / Desktop`
- `Reports / Desktop`
- `Settings / Desktop`

Add tablet variants after desktop structure is approved.

### `03 High-Fidelity Screens` -> `1:4`

Create polished frames with the same page names and parallel tablet variants:

- `Login / Desktop / HiFi`
- `Overview Dashboard / Desktop / HiFi`
- `Alerts / Desktop / HiFi`
- `Alert Detail / Desktop / HiFi`
- `Incidents Queue / Desktop / HiFi`
- `Assets / Desktop / HiFi`
- `Response History / Desktop / HiFi`
- `Rules Policies / Desktop / HiFi`
- `Reports / Desktop / HiFi`
- `Settings / Desktop / HiFi`

High-fidelity screens should directly reference the token and component names in this document and in the design spec so React implementation stays faithful.

## 7. Source Of Truth Order

Until Figma canvas editing is available again, use this priority order:

1. [AGENTS.md](/C:/Users/nimus/OneDrive/Documents/GitHub/Aegiscore-Main/AGENTS.md)
2. [docs/frontend/aegiscore-design-spec.md](/C:/Users/nimus/OneDrive/Documents/GitHub/Aegiscore-Main/docs/frontend/aegiscore-design-spec.md)
3. [docs/frontend/component-inventory.md](/C:/Users/nimus/OneDrive/Documents/GitHub/Aegiscore-Main/docs/frontend/component-inventory.md)
4. Existing app shell and frontend implementation in [apps/web](/C:/Users/nimus/OneDrive/Documents/GitHub/Aegiscore-Main/apps/web)
