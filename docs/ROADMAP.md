# LinkPulse roadmap

Status reflects planning only; items are not marked complete until implemented and tested.

## Phase 0 — Product and engineering foundation
- [ ] Confirm product requirements and user personas
- [ ] Validate competitor gaps and open-source license choice
- [x] Establish repository conventions, CI workflow, and API regression-test suite (CI execution still to be verified)
- [ ] Add linting, coverage thresholds, and migration tests
- [ ] Define threat model, privacy model, and data retention defaults

## Phase 1 — Link management
- [ ] Workspace and project model
- [x] Link create, update, archive, and redirect (initial API slice)
- [x] Custom aliases (initial slug support) and UTM URL builder API
- [ ] Persist campaign metadata and expose UTM builder in dashboard
- [x] PNG QR generation API and active-link dashboard action
- [ ] SVG/PDF export and QR management
- [x] Expiry and click-limit enforcement
- [ ] Password-protected links
- [ ] Bulk CSV import/export

## Phase 2 — Click intelligence
- [x] Initial click event collection (timestamp, referrer host, coarse device class; advanced classification pending)
- [x] Basic bot/link-preview classification with separate counts (advanced detection and filtering pending)
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
- [x] Initial responsive campaign workspace dashboard
- [ ] Campaign comparisons and advanced dashboard filters
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