# Supported detection scope (product)

AegisCore’s **academic MVP** validates **four** threat categories end-to-end:

- `brute_force`
- `port_scan`
- `file_integrity_violation`
- `unauthorized_user_creation`

**Standard description:** The release covers brute-force attacks, port scans, file integrity violations, and unauthorized user account creation. **Additional detection categories are roadmap items**, not part of this implementation.

Analyst review order in the console: **alerts and evidence** → **severity and risk score** → **automated responses** → **incidents** and notifications.

Canonical definition: [final-product.md](../final-product.md). Frontend constants: `apps/web/src/lib/supportedDetections.ts`.
