# LinkPulse architecture (proposed)

## System context

```text
Browser / Mobile App / QR
          |
          v
   Redirect + Click API ---------> PostgreSQL
          |                            ^
          |                            |
          v                            |
   Event Queue / Worker                |
          ^                            |
          |                            |
 Business Event API -------------------+
          |
          v
 Funnel + Attribution Queries
          |
          v
 Dashboard / CSV Export / Webhooks
```

## Proposed components

- **Web application:** Next.js and TypeScript for workspace, link management, dashboards, and configuration.
- **API service:** FastAPI for authentication, link CRUD, redirects, event ingestion, reporting, and exports.
- **Relational store:** PostgreSQL for workspaces, projects, links, click events, business events, attribution settings, and audit records.
- **Worker layer:** Redis-backed queue for aggregation, bot classification, webhook delivery, and scheduled reports.
- **Deployment:** Docker Compose for a first self-hosted installation; production orchestration can follow after operational needs are validated.

## Core domain entities

- Workspace
- Project
- API key (store only a secure hash)
- Link
- Click event
- Business event
- Campaign / UTM metadata
- Funnel definition
- Attribution rule
- Webhook endpoint and delivery attempt
- Audit event

## Event contract principles

Every event should carry an event ID, event type, event timestamp, project identifier, and an idempotency key. Optional fields can include link ID, anonymous session token, campaign metadata, and explicitly permitted business attributes.

Do not collect names, email addresses, phone numbers, payment credentials, or other direct identifiers unless a clearly justified, documented use case and lawful basis exist. Prefer opaque business references and minimise payload retention.

## Attribution rules

- Keep click events and conversion events distinct.
- Deduplicate using stable event IDs / idempotency keys.
- Make attribution window and model configurable and visible.
- Preserve event timestamps and ingestion timestamps separately.
- Mark attribution as unavailable when required evidence is missing.
- Never infer transaction value or revenue from a click.
- Support first-touch and last-touch only after deterministic event linkage is implemented; label model outputs clearly.

## Security and operations

- Hash API keys; show secrets only once.
- Enforce project-level authorization on every read and write.
- Validate payload size and schema.
- Rate-limit public redirect and ingestion endpoints.
- Avoid logging raw sensitive payloads or secrets.
- Provide configurable retention and deletion workflows.
- Record administrative changes in an audit log.
- Add migrations, backups, health checks, and observability before production use.

This document describes a proposed architecture. It is not evidence that these components have been implemented.