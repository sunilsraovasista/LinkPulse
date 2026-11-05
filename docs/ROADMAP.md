# LinkPulse roadmap

Status reflects planning only; items are not marked complete until implemented and tested.

## Phase 0 — Product and engineering foundation
- [ ] Confirm product requirements and user personas
- [ ] Validate competitor gaps and open-source license choice
- [ ] Establish repository conventions, CI, linting, and test strategy
- [ ] Define threat model, privacy model, and data retention defaults

## Phase 1 — Link management
- [ ] Workspace and project model
- [x] Link create and redirect (initial API slice; update/archive still pending)
- [ ] Custom aliases and UTM metadata
- [ ] QR code generation
- [ ] Expiry and password-protected links
- [ ] Bulk CSV import/export

## Phase 2 — Click intelligence
- [x] Initial click event collection (timestamp, referrer host, coarse device class; advanced classification pending)
- [ ] Bot and crawler classification
- [ ] Deduplication and aggregation
- [ ] Referrer and coarse device/browser reporting
- [ ] Privacy controls and retention jobs

## Phase 3 — Business events and funnels
- [ ] API-key-authenticated event ingestion
- [ ] Idempotency and event validation
- [ ] Configurable funnel definitions
- [ ] Verified conversion reporting
- [ ] Transparent attribution windows and models

## Phase 4 — Reporting and integrations
- [ ] Campaign dashboard and comparisons
- [ ] CSV export and scheduled reports
- [ ] Webhooks with retries and signing
- [ ] SDKs and integration examples

## Phase 5 — Production readiness
- [ ] Security review and dependency scanning
- [ ] Load and reliability testing
- [ ] Backup/restore validation
- [ ] Deployment guide and operational runbooks
- [ ] Accessibility and usability review

## Release gate

No feature should be described as production-ready until its tests, security implications, failure modes, documentation, and deployment path have been reviewed.