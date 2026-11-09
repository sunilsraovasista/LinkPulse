# LinkPulse

**Open-source campaign, conversion and business-event intelligence.**

LinkPulse helps teams understand what happens after someone clicks a campaign link. It combines link management, privacy-conscious click measurement, QR campaigns, and verified downstream business events into one self-hostable analytics platform.

> **Core promise:** connect campaign touchpoints to measurable outcomes—with transparent attribution and data ownership.

## Product principles

- **Open source and self-hostable:** the core product should run on infrastructure controlled by its users, without mandatory subscriptions or artificial self-hosted limits.
- **Evidence before attribution:** clicks are not conversions. Revenue or conversion claims require verified business events.
- **Privacy by design:** data minimisation, configurable retention, consent-aware tracking, and no covert fingerprinting.
- **Portable data:** documented APIs and straightforward exports.
- **Industry-aware, not industry-locked:** a common event and funnel engine supports different business models.

## Planned capabilities

1. **Link management** — short links, custom aliases, UTM parameters, expiry, password protection, QR codes, and bulk CSV operations.
2. **Click intelligence** — aggregated campaign performance, referrers, coarse device/browser insights, bot filtering, and deduplication.
3. **Business events** — receive events such as signup, order paid, demo attended, refund, or settlement through an API, SDK, or webhook.
4. **Funnels and attribution** — configurable conversion windows and transparent attribution rules, with clear treatment of missing or unverified events.
5. **Reporting and exports** — campaign dashboards, scheduled evidence-backed reports, CSV exports, and integrations.
6. **Developer platform** — documented REST API, webhooks, and lightweight SDKs.

## Example workflows

- **Education:** campaign click → lead → demo booked → demo attended → enrolment.
- **Food delivery:** campaign click → menu view → checkout → paid order → fulfilled order.
- **Cross-border payments:** campaign click → payment initiated → authorised/failed → refund → settlement. LinkPulse is analytics infrastructure, not a payment processor.
- **Devotional services:** campaign click → service view → booking → payment → completed service.

These are illustrative workflows, not claims about integrations or verified customer pain points. Real company integrations require authorised access to their event data. Demo data must be labelled as synthetic.

## Architecture direction

- Frontend: Next.js + TypeScript
- API: Python + FastAPI
- Data: PostgreSQL
- Background processing: Redis + worker queue
- Deployment: Docker / Docker Compose
- Analytics: SQL-first event model with export-friendly reporting

Technology choices will be validated as implementation progresses.

## AI growth strategist (v1)

The API exposes `GET /api/strategy/growth`, a deterministic recommendation baseline based on recorded click telemetry. It flags potential traffic-quality, referrer-coverage, device-mix, channel-concentration and weekly movement signals. It does not claim conversions, customers or revenue. This endpoint is not an LLM-powered autonomous agent and must remain behind the development-only service boundary until authentication and workspace isolation are implemented. See [Growth Strategist v1](docs/GROWTH_STRATEGIST_V1.md).

## Development status

The repository now includes a first runnable FastAPI development slice for creating short links, redirecting visitors, and recording privacy-minimised click metadata, with per-link and overview analytics. It is not yet production-ready: authentication, workspace isolation, PostgreSQL migrations, custom-domain verification, advanced bot exclusion, retention controls, business-event ingestion, and conversion attribution remain unimplemented. PNG QR generation is available, but SVG/PDF exports are pending. Production startup is deliberately blocked until the security and data-isolation foundation is implemented. No public deployment or external integrations are claimed. See [API quick start](backend/README.md).

See [Product vision](docs/PRODUCT_VISION.md), [Architecture](docs/ARCHITECTURE.md), [Roadmap](docs/ROADMAP.md), and [Security and privacy](SECURITY.md).

## License

License selection is **not yet final**. Review AGPL-3.0 and Apache-2.0 trade-offs before publishing a license file.
