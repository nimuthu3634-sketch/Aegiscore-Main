# AegisCore Frontend Design Specification

## Purpose

This document turns the confirmed Figma file structure into a repo-based design blueprint so the frontend can proceed without direct Figma canvas editing in this session.

Confirmed Figma blueprint:

- `00 Cover` -> `0:1`
- `01 Design System` -> `1:2`
- `02 Wireframes` -> `1:3`
- `03 High-Fidelity Screens` -> `1:4`

The implementation order for frontend work should stay aligned to that blueprint:

1. Define tokens and reusable UI rules from `01 Design System`
2. Build page structure from `02 Wireframes`
3. Refine visual behavior from `03 High-Fidelity Screens`

## 1. Brand Overview

AegisCore is a premium, single-tenant SOC platform for SMEs. The UI should feel like a real operations console: calm under pressure, high-contrast, dense enough for analysts, and intentionally minimal. It should not read like a marketing site or a generic admin template.

Brand principles:

- Dark-first interface with strong contrast and restrained accent usage
- Orange is the product identity color, not a decorative highlight used everywhere
- Primary surfaces should feel technical, solid, and focused
- Data should be easy to scan in dense tables without visual clutter
- Analyst workflows should prioritize signal clarity, evidence traceability, and decisive actions
- The AegisCore logo should appear in the authentication shell, primary sidebar brand area, and any exported report cover or report header

## 2. Color Tokens

Use the provided brand palette as the only base color system. Additional shades should come from opacity overlays, borders, and subtle surface layering rather than new hues.

### Core Tokens

| Token | Value | Usage |
| --- | --- | --- |
| `color.brand.primary` | `#F97316` | Primary action, selected nav state, active chart trend, focused highlights |
| `color.brand.primaryHover` | `#EA580C` | Primary hover, pressed state, active icon hover |
| `color.bg.base` | `#0A0A0A` | App background, page canvas, auth shell background |
| `color.bg.panel` | `#111827` | Panels, cards, sidebars, tables, modals |
| `color.border.default` | `#1F2937` | Dividers, card borders, table grid lines, input borders |
| `color.text.primary` | `#F9FAFB` | Primary heading and body text |
| `color.text.secondary` | `#D1D5DB` | Secondary body text, helper text, less prominent labels |
| `color.text.muted` | `#9CA3AF` | Tertiary metadata, timestamps, disabled icon color |
| `color.state.danger` | `#EF4444` | Critical alerts, destructive actions, failed responses |
| `color.state.success` | `#22C55E` | Successful response actions, healthy integrations, resolved states |
| `color.state.warning` | `#F59E0B` | Elevated risk, degraded integration health, pending states |

### Semantic Surface Guidance

| Token | Formula | Usage |
| --- | --- | --- |
| `color.surface.canvas` | `#0A0A0A` | Base app background |
| `color.surface.panel` | `#111827` | Primary content blocks |
| `color.surface.panelRaised` | `rgba(17, 24, 39, 0.92)` | Floating cards and dropdowns |
| `color.surface.panelSubtle` | `rgba(17, 24, 39, 0.76)` | Secondary cards and nested sections |
| `color.surface.overlay` | `rgba(10, 10, 10, 0.72)` | Modal scrim and focused overlays |
| `color.surface.accentSoft` | `rgba(249, 115, 22, 0.12)` | Active list rows, selected pill background, subtle chart callouts |
| `color.surface.successSoft` | `rgba(34, 197, 94, 0.12)` | Success badges and completed state backgrounds |
| `color.surface.warningSoft` | `rgba(245, 158, 11, 0.12)` | Warning chips and pending state backgrounds |
| `color.surface.dangerSoft` | `rgba(239, 68, 68, 0.12)` | Critical chips, destructive alerts, failed state backgrounds |

### Color Usage Rules

- Keep orange concentrated around primary actions, current selections, and the most important trend line or KPI on a screen.
- Do not use green, amber, or red as generic decoration. Reserve them for outcome states and risk communication.
- Charts should use orange for the primary series, then warning, danger, success, and muted gray only as needed.
- Backgrounds should stay within black and dark-panel ranges. Avoid light panels, white cards, or pale gray admin styling.
- Borders should be present more often than shadows to maintain the sharp SOC-console feel.

## 3. Typography System

The type system should balance two needs: bold, memorable headings for command-center hierarchy and compact, highly legible UI text for dense security workflows.

### Font Families

| Role | Family | Fallback |
| --- | --- | --- |
| Display and page titles | `"Space Grotesk"` | `"Segoe UI", sans-serif` |
| UI text and controls | `"Inter"` | `"Segoe UI", sans-serif` |
| Technical data and metadata | `"JetBrains Mono"` | `"Consolas", monospace` |

### Type Scale

| Token | Size / Line Height | Weight | Use |
| --- | --- | --- | --- |
| `type.display.lg` | `40 / 48` | `600` | Login hero, dashboard overview titles, report covers |
| `type.display.md` | `32 / 40` | `600` | Incident titles, page hero headers |
| `type.heading.lg` | `24 / 32` | `600` | Section titles, page titles |
| `type.heading.md` | `20 / 28` | `600` | Panel titles, modal titles |
| `type.heading.sm` | `16 / 24` | `600` | Card titles, form section titles |
| `type.body.md` | `14 / 22` | `400` | Default body copy, descriptions, table cells |
| `type.body.sm` | `13 / 20` | `400` | Dense list rows, helper text, filter labels |
| `type.label.md` | `12 / 16` | `600` | Button labels, nav labels, table headers |
| `type.label.sm` | `11 / 16` | `600` | Overlines, chips, secondary metadata labels |
| `type.mono.md` | `13 / 20` | `500` | IPs, hashes, hostnames, ports, timestamps in detail views |
| `type.mono.sm` | `12 / 18` | `500` | Table monospace cells, compact event metadata |

### Typography Rules

- Use display styles sparingly. Most pages should open with `type.heading.lg` or `type.display.md`, not giant marketing-style hero text.
- Incident and alert titles should be concise, high-contrast, and paired with severity or status chips rather than long subtitle stacks.
- Table headers should always use `type.label.md` in uppercase or tracked small caps only when the header bar is short and stable.
- Raw telemetry, IP addresses, hashes, ports, and timestamps should use the mono family for scanability and alignment.
- Avoid long paragraph blocks. Most product copy should be short, practical, and action-oriented.

## 4. Spacing Scale

Use a 4px base grid with denser spacing inside tables and filter bars.

| Token | Value | Use |
| --- | --- | --- |
| `space.0` | `0px` | Reset |
| `space.1` | `4px` | Tight icon gap, fine label spacing |
| `space.2` | `8px` | Chip padding, small grouped controls |
| `space.3` | `12px` | Compact form spacing, metadata groups |
| `space.4` | `16px` | Default internal card padding step |
| `space.5` | `20px` | Medium card spacing, toolbar padding |
| `space.6` | `24px` | Standard panel padding, section gap |
| `space.8` | `32px` | Major page section separation |
| `space.10` | `40px` | Dashboard region spacing |
| `space.12` | `48px` | Auth layouts, report sections |
| `space.16` | `64px` | Large composition margins |

Spacing rules:

- Cards should generally use `24px` internal padding on desktop and `20px` on tablet.
- Table toolbars can compress to `16px` vertical rhythm for density.
- Sidebar item spacing should feel compact and deliberate rather than airy.
- Avoid large vertical whitespace that makes data screens feel empty or consumer-app-like.

## 5. Border Radius Scale

The interface should feel sharp, not overly soft. Use restrained radii.

| Token | Value | Use |
| --- | --- | --- |
| `radius.none` | `0px` | Hard dividers, chart fills, image masks when needed |
| `radius.sm` | `6px` | Chips, inline badges, compact inputs |
| `radius.md` | `10px` | Buttons, inputs, dropdowns |
| `radius.lg` | `14px` | Cards, tables, small modals |
| `radius.xl` | `18px` | Major panels, auth containers, large modal shells |
| `radius.full` | `999px` | Pills and segmented selection chips |

Radius rules:

- Primary panels should stay within `14px` to `18px`.
- Buttons and inputs should not exceed `10px`.
- Avoid very round consumer-app cards or bubble styling.

## 6. Shadow And Elevation Guidance

Elevation should be subtle and layered on top of borders, not used as a substitute for structure.

| Token | Shadow | Usage |
| --- | --- | --- |
| `shadow.panel` | `0 10px 30px rgba(0, 0, 0, 0.28)` | Standard dashboard cards |
| `shadow.float` | `0 18px 40px rgba(0, 0, 0, 0.38)` | Dropdowns, flyouts, raised utility panels |
| `shadow.modal` | `0 24px 64px rgba(0, 0, 0, 0.46)` | Modal dialogs |
| `shadow.focus` | `0 0 0 1px rgba(249, 115, 22, 0.65), 0 0 0 4px rgba(249, 115, 22, 0.16)` | Keyboard focus, selected control emphasis |

Elevation rules:

- Most panels should have both a visible border and a soft shadow.
- Orange glow should be used only for focus or active selection, not always-on decoration.
- Critical or error states should use border and soft background changes before stronger shadow changes.

## 7. Iconography Guidance

The icon system should feel technical and precise.

- Use a clean, line-based icon family with a consistent 2px stroke.
- Default sizes:
  - `16px` for inline metadata
  - `18px` for nav rows and chips
  - `20px` for buttons, headers, and cards
  - `24px` for empty states and hero indicators
- Use monochrome icon styling by default.
- Orange icons should be limited to active navigation, primary CTAs, and high-value dashboard highlights.
- Status icons may use success, warning, or danger color only when reinforcing actual state.
- Prefer security-relevant iconography: shield, pulse, endpoint, network, alert, incident, policy, history, report, settings.
- Avoid filled, playful, or multi-color icon sets.

## 8. Data Display Rules For SOC UI

SOC data is dense and time-sensitive. The UI must preserve context while supporting quick scanning.

- Always show source system on alerts and incidents, at minimum `Wazuh` or `Suricata`.
- Severity, status, and risk score must appear together near the top of alert and incident views.
- Present timestamps in absolute form first and optionally relative second.
- Use monospace formatting for:
  - IP addresses
  - usernames in raw event contexts
  - file paths when rendered as evidence
  - hashes
  - ports
  - raw event IDs
  - timestamps in timelines and evidence tables
- Keep raw source payloads available in detail screens inside a collapsible, searchable block.
- Group evidence into clear sections: summary, affected asset, source, related events, raw payload, audit history.
- Dense pages should use compact rows and consistent alignment instead of reducing contrast.
- Investigation views should preserve visible history and action trace, not hide important chronology behind multiple dialogs.

## 9. Table Design Rules

Tables are the primary operating surface for alerts, incidents, assets, and response history.

### Table Anatomy

- Outer container: bordered panel using `color.bg.panel`, `color.border.default`, `radius.lg`
- Header bar: title, count, filter summary, export or quick action area
- Filter row: search, source filter, severity filter, status filter, date range, clear filters
- Column header row: sticky when the table scrolls
- Body rows: hover highlight, selected state, optional inline action menu
- Footer: pagination or virtualized range summary

### Row Behavior

- Default row height: `52px`
- Dense row height: `44px` for history and evidence views
- Hover state: soft panel raise plus `color.surface.accentSoft`
- Selected state: left accent rule in orange plus subtle orange-tinted background
- Critical or failed rows should not fully recolor the row; instead use chips and one supporting indicator

### Table Content Rules

- Left-align all text except counts and numeric KPI columns
- Use mono styles for telemetry columns
- Keep per-row actions compact and discoverable
- Do not place more than two inline actions per row before using an overflow menu
- Use consistent column ordering:
  - Alerts: time, source, detection, severity, risk, asset, status, assignee
  - Incidents: opened, title, severity, related alerts, owner, status, last activity
  - Assets: hostname, IP, environment, alert count, last seen, health
  - Response History: executed at, action, target, actor, outcome, incident

## 10. Chart Card Rules

Charts should support decision-making, not act as decorative infographics.

### Card Anatomy

- Overline or section label
- Card title
- One supporting KPI or insight sentence
- Time range or source context
- Main chart area
- Minimal legend or callout list

### Chart Guidance

- Preferred chart types:
  - Area or line chart for alert volume over time
  - Stacked bar chart for severity by source or detection type
  - Horizontal bar chart for asset exposure or incident status distribution
  - Small sparklines inside metric cards when trend context matters
- Avoid pie-heavy dashboards. Use donut charts only when the split is simple and there are at most three categories.
- Use orange for the primary trend or selected series.
- Use success, warning, and danger only when the data encodes health or risk.
- Grid lines should be subtle, using `color.border.default`.
- Tooltip panels should look like mini dark cards, not default chart tooltips.

## 11. Sidebar And Top Nav Rules

### Sidebar

- Desktop width: `264px`
- Tablet width: `80px` collapsed or drawer-based depending on available space
- Structure:
  - Brand block with logo and environment label
  - Primary nav
  - Utility nav near the bottom
  - Session / user block

Primary nav order:

1. Overview Dashboard
2. Alerts
3. Incidents Queue
4. Assets / Endpoints
5. Response History
6. Rules / Policies
7. Reports
8. Settings

Sidebar rules:

- Active item: orange left indicator plus tinted background
- Hover item: subtle panel raise and brighter text
- Badge counts may appear on Alerts and Incidents
- Keep item labels short and operational
- Avoid oversized logo or brand treatments that consume vertical space

### Top Navigation

- Height: `64px`
- Contents:
  - Page title and short supporting subtitle
  - Global search or quick command entry
  - Time range or environment context when relevant
  - API or ingestion health indicator
  - User menu

Top-nav rules:

- Keep it anchored and visually lighter than the sidebar
- Do not overload it with secondary filters that belong in page toolbars
- Search should support alert IDs, incident IDs, asset names, IPs, and usernames

## 12. Badge And Chip System

Use compact chips to encode status without overwhelming the table or header.

### Badge Types

| Component | Use | Example Values |
| --- | --- | --- |
| Source badge | Event or alert origin | `Wazuh`, `Suricata` |
| Detection badge | In-scope detection type | `brute_force`, `port_scan` |
| AI badge | AI-scored or analyst-reviewed flag | `AI scored`, `Reviewed` |
| Environment badge | Asset grouping | `production`, `office`, `remote` |

### Severity Chips

| Level | Visual Rule |
| --- | --- |
| Critical | `color.state.danger` text and border on `color.surface.dangerSoft` |
| High | `color.state.warning` text and border on `color.surface.warningSoft` |
| Medium | `color.brand.primary` text and border on `color.surface.accentSoft` |
| Low | `color.text.secondary` text with muted border on `rgba(156, 163, 175, 0.12)` |

### Status Chips

| Status | Visual Rule |
| --- | --- |
| New | muted background with bright text |
| Triaged | orange-tinted background |
| Investigating | warning-tinted background |
| Contained | success-tinted background |
| Resolved | success-tinted background with lower emphasis than contained |
| Pending Response | warning-tinted background |
| Failed | danger-tinted background |
| Disabled | muted gray with low-contrast border |

Chip rules:

- Chips should be compact, uppercase optional, and visually stable across tables and headers.
- Do not mix more than three chips in a single compact row before collapsing extras into metadata.
- Risk score chips should pair number plus label, for example `87 High`.

## 13. Form And Modal Rules

Forms and policy configuration need to feel operational rather than consumer-friendly.

### Forms

- Labels should sit above fields, not inside them as the only identifier.
- Helper text should explain impact, not repeat label names.
- Required destructive or high-impact controls should include inline warnings before submission.
- Use section cards for grouped settings rather than one long flat form.
- Field spacing:
  - `12px` between label and input
  - `16px` within grouped fields
  - `24px` between form sections
- Inputs should support dense usage without looking cramped.

### Input Variants

- Text input
- Password input
- Search input
- Select
- Multi-select
- Toggle / switch
- Text area for notes, investigation comments, and policy descriptions
- Read-only key-value field for immutable telemetry

### Modals

- Use modals for:
  - confirm response action
  - assign incident
  - create or edit policy
  - export or generate report
- Avoid modal-over-modal flows.
- Modal sizes:
  - Small `480px`: confirmations
  - Medium `720px`: edit forms
  - Large `960px`: complex workflows or evidence comparison
- The footer should keep the primary action on the right and the safe exit on the left.

## 14. Empty, Loading, And Error States

### Empty States

- Use a minimal icon or illustration with a dark-panel card, not large marketing-style artwork.
- Include:
  - practical title
  - one short explanatory line
  - one primary CTA
  - optional secondary action
- Examples:
  - no alerts in current filter
  - no incidents assigned
  - no reports generated yet

### Loading States

- Prefer skeleton rows and skeleton cards over centered spinners for page content.
- Skeleton layouts should mirror the final page structure closely.
- Long-running data tasks may add a compact inline spinner in the toolbar or card header.

### Error States

- Keep the surrounding layout intact when possible.
- Use bordered error panels with danger-tinted accents rather than full-screen crashes.
- Show:
  - what failed
  - likely scope of impact
  - retry action
  - link or toggle to diagnostic detail when appropriate

## 15. Page-By-Page Layout Specifications

All pages are desktop-first, optimized for `1280px` and wider. Tablet layouts should preserve hierarchy using stacked sections, drawer navigation, and fewer simultaneous panels.

### Login

Purpose:

- Authenticate analysts and administrators into the single-tenant SOC

Desktop layout:

- Split-screen shell
- Left side: brand narrative, product positioning, trust copy, optional security-status highlights
- Right side: login card with logo, title, environment label, username, password, sign-in CTA, support text

Key UI rules:

- Use the logo prominently but not oversized
- The login card should float on a deep black or layered dark background
- Keep the form compact and high-contrast
- Provide space for API or environment status if needed later

Tablet behavior:

- Collapse to a centered auth card with background branding reduced to a top banner or subtle side panel

### Overview Dashboard

Purpose:

- Give analysts an immediate view of platform health, alert pressure, active incidents, response backlog, and investigation priorities

Desktop layout:

- App shell with sidebar and top nav
- Header row with page title, timeframe, health status, and quick search
- KPI row:
  - normalized alerts
  - open incidents
  - pending responses
  - monitored assets
- Main content grid:
  - alert volume chart
  - severity by detection or source
  - active incidents queue snapshot
  - response history snapshot
  - high-risk assets or watchlist
  - analyst note or investigation feed

Key UI rules:

- The primary hero chart should use orange as the dominant data accent
- Keep dashboard cards modular and comparable in height
- At least one panel should surface AI or risk-scoring insight in plain language

Tablet behavior:

- Collapse to single-column chart stacking with KPI cards in a two-column grid

### Alerts

Purpose:

- Provide a high-density triage surface for normalized alerts

Desktop layout:

- Page header with total count and filter summary
- Toolbar with search, source filter, severity filter, status filter, date range, reset controls
- Main table for normalized alerts
- Optional right-side preview drawer or inline row expansion for summary detail

Key UI rules:

- Optimize for fast sorting and bulk scanning
- Surface source, detection type, severity, risk, affected asset, and status without opening the detail page
- Keep row actions minimal: assign, open incident, inspect

Tablet behavior:

- Reduce visible columns and use row expansion for secondary metadata

### Alert / Incident Detail

Purpose:

- Support investigation workflow visibility, evidence review, risk explanation, and response decisions

Desktop layout:

- Header with title, severity chip, status chip, source badge, timestamps, assignee, primary actions
- Two-column content:
  - Main column: summary, timeline, evidence, related alerts, notes
  - Side column: risk score, asset summary, response recommendations, response actions, audit summary
- Secondary tab or segmented sections:
  - Overview
  - Timeline
  - Evidence
  - Raw Payload
  - Audit History

Key UI rules:

- Raw payload must remain accessible but visually separate from the primary narrative
- Show the reason behind risk scoring in a concise card
- Make response actions visible but not easy to trigger accidentally
- Preserve chronology and change history throughout the page

Tablet behavior:

- Stack the side column beneath the main investigation flow

### Incidents Queue

Purpose:

- Manage active investigation workload across open and triaged incidents

Desktop layout:

- Header with open counts, priority mix, and team ownership summary
- Filter bar for severity, owner, status, source, last activity
- Main queue table or split list
- Optional right-side incident snapshot panel for currently selected row

Key UI rules:

- Incident title, severity, owner, status, related alert count, and last update must be visible at a glance
- SLA-like timing should appear as a subtle urgency indicator, not bright noise
- Bulk management should remain available for assignment and status changes

Tablet behavior:

- Replace side snapshot panel with an expandable row or drawer detail pattern

### Assets / Endpoints

Purpose:

- Show monitored assets, their exposure, recent alert activity, and operational context

Desktop layout:

- Header with total assets, unhealthy assets, and recent activity indicators
- Filter toolbar for environment, health, operating system, and alert volume
- Asset inventory table
- Optional asset detail side panel with:
  - hostname
  - IP addresses
  - recent alerts
  - last seen
  - open incidents

Key UI rules:

- Hostnames and IPs should be easy to compare and copy
- Asset detail should connect directly to incidents and recent alerts
- Keep the SME focus: inventory should remain practical, not overloaded with enterprise CMDB concepts

Tablet behavior:

- Promote the detail panel into a full-width drawer

### Response History

Purpose:

- Show a trustworthy timeline of manual and automated response actions

Desktop layout:

- Header with recent success rate, pending items, and failed action count
- Filters for action type, actor, status, target, and time range
- Main response history table
- Optional grouped timeline by incident

Key UI rules:

- Every action row should clearly show who triggered it, what target changed, and the outcome
- Use success, warning, and danger only for actual execution result
- Preserve rollback or follow-up guidance where available

Tablet behavior:

- Use condensed filters and a simpler table with row details for extended metadata

### Rules / Policies

Purpose:

- Manage in-scope detection and response policies without expanding beyond the approved product scope

Desktop layout:

- Left-side rules list or table
- Right-side detail or edit panel for the selected policy
- Top header with create policy action and scope reminder

Policy scope for v1:

- `brute_force`
- `file_integrity_violation`
- `port_scan`
- `unauthorized_user_creation`

Key UI rules:

- Make it obvious which policies are detection-only and which include automated response
- Use clear safeguards for high-impact response actions
- Keep policy editing structured around thresholds, matching logic, actions, and audit notes

Tablet behavior:

- Switch to list-first navigation with policy detail on a separate view or drawer

### Reports

Purpose:

- Provide operational summaries for SMEs without enterprise reporting complexity

Desktop layout:

- Header with report templates and generation actions
- Report template cards or table
- Recent report history table
- Secondary panel for generation filters or preview metadata

Key UI rules:

- Focus on practical reports:
  - alert trends
  - incident summaries
  - asset exposure snapshots
  - response execution summaries
- Avoid overly decorative charts or slide-like presentation layout

Tablet behavior:

- Stack templates above recent report history

### Settings

Purpose:

- Configure the single-tenant platform, integrations, auth behavior, notifications, and retention settings

Desktop layout:

- Settings sub-navigation on the left
- Main form panel on the right
- Group sections into:
  - organization and branding
  - integrations
  - auth and sessions
  - notifications
  - retention and audit

Key UI rules:

- Keep settings modular with clear save boundaries
- Integration settings should emphasize backend ownership of Wazuh and Suricata connections
- Avoid enterprise multi-tenant billing or workspace concepts

Tablet behavior:

- Convert settings nav into a segmented control or drawer

## Implementation Notes

- Build the UI with React, TypeScript, Tailwind CSS, and Recharts.
- Keep all frontend data access behind backend APIs.
- Preserve raw payload visibility, history visibility, and investigation context in screen-level components.
- Use this document as the design source of truth until direct Figma editing becomes available again.
