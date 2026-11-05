# LinkPulse release criteria

No milestone is complete because its UI exists. Every capability must pass functional, security, privacy, reliability and operator checks.

## Link-management release
- Create, read, update, archive and redirect links.
- Reject unsafe destination schemes and malformed aliases.
- Prevent slug collisions and enforce ownership.
- Handle expiry, click limits and protected links correctly.
- QR output is scannable and points to the managed short link.
- UTM values are encoded correctly and do not corrupt existing query strings.

## Analytics release
- Click events have stable IDs and timestamps.
- Bot/crawler traffic is identified separately from human traffic.
- Repeated requests and preview fetches are not silently represented as unique people.
- Referrer/device breakdowns document unknown and unavailable values.
- Timezone and date-range filters are tested.
- Export totals reconcile with dashboard totals.

## Business-event and attribution release
- Ingestion is authenticated, schema-validated, rate-limited and idempotent.
- Events distinguish occurrence time from ingestion time.
- Invalid, duplicate, late and unmatched events are visible.
- Attribution windows and models are explicit and configurable.
- Revenue is reported only from verified business events and currency is preserved.
- Every attributed result can be traced to its source click and conversion event.

## Organisation and security release
- Every data query is scoped to the authenticated workspace/project.
- Roles and permissions are tested for both allowed and denied actions.
- Secrets are hashed or encrypted appropriately and never logged.
- Webhooks use signatures, replay protection and bounded retries.
- Retention, deletion, export and backup/restore are tested.
- Rate limits, abuse controls and redirect safety are in place.
- Threat model, dependency scan and security review are complete.

## Production operations release
- Automated unit, integration and migration tests run in CI.
- Load tests cover redirect throughput and event ingestion.
- Health/readiness checks, structured logs and metrics are available.
- Backup/restore and upgrade procedures are documented and tested.
- Deployment instructions cover environment variables, TLS, database and worker services.
- Accessibility and responsive UI checks pass.

## Current milestone status

The first API slice is development-only. It supports link creation, redirects and basic click analytics on SQLite. It is not a production release and does not satisfy the criteria above.
