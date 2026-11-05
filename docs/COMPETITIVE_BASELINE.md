# LinkPulse competitive baseline

Research snapshot: 5 November 2026. This is a product capability comparison, not a claim that LinkPulse currently matches these features.

## Linkly capability baseline

Linkly's public feature material describes:
- Branded short links, custom domains and vanity aliases.
- Dynamic QR codes with customisation and downloadable formats.
- Real-time click reporting with time, geography, device, browser and referrer dimensions.
- UTM construction, conversion tracking and advertising/retargeting tags.
- Geo/device/language routing, app redirects, link rotation and A/B distribution.
- Expiring, click-limited and password-protected links.
- REST API, webhooks, automation integrations, exports and team/workspace capabilities.
- Bulk link operations and reporting.

Sources:
- https://linklyhq.com/features
- https://linklyhq.com/support/how-linkly-works
- https://linklyhq.com/pricing

## LinkPulse parity requirements

| Capability | LinkPulse target | Current implementation |
|---|---|---|
| Create short links and aliases | Required | Initial API only |
| Redirect and click capture | Required | Implemented in development slice |
| Per-link and overview analytics | Required | Basic totals, referrer host, coarse device |
| Custom domains and DNS verification | Required | Not implemented |
| Dynamic QR designer and exports | Required | Not implemented |
| UTM builder and campaign tagging | Required | Not implemented |
| Geo/device/language routing | Required | Not implemented |
| Expiry, click limits, password protection | Required | Not implemented |
| Bot/crawler detection and filtering | Required | Basic user-agent classification only; not excluded |
| Conversion tracking and revenue attribution | Required, evidence-backed | Not implemented |
| REST API and API keys | Required | Not implemented |
| Signed webhooks and retries | Required | Not implemented |
| Bulk import/export | Required | Not implemented |
| Team roles, workspaces and audit log | Required | Not implemented |
| Data retention, consent controls and privacy modes | Required | Not implemented |
| Self-hosting and operational tooling | Required | Docker Compose development setup only |

## Differentiation beyond link shortening

LinkPulse should not claim to win by adding more redirect rules alone. Its strategic layer is a verified business-event pipeline:
1. Campaign click creates a first-party LinkPulse click reference.
2. A product, commerce, CRM or operations system sends a business event using an idempotent event ID.
3. LinkPulse validates the event and preserves source evidence.
4. A configurable funnel connects click cohorts to outcomes.
5. Reports distinguish directly observed events, deterministic links, modelled attribution and unknown outcomes.

Examples include lead qualified, demo attended, subscription activated, order fulfilled, payment settled and refund completed. LinkPulse must not process payments or store payment credentials.

## Segment fit

- **Early-stage startups:** fast setup, free/self-hosted core, simple campaign links, QR, clear weekly reports, low operational burden and API-first onboarding.
- **Growing businesses:** multiple brands/projects, team permissions, campaign comparisons, bulk operations, webhooks and CRM/commerce event connectors.
- **Mid-sized organisations:** role-based access, audit history, SSO option, environment separation, custom domains, retention policies, data exports, backups, monitoring, documented APIs and predictable scaling.

Do not make enterprise controls a prerequisite for a small team. Keep the product progressively adoptable.
