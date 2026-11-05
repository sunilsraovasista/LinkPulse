# LinkPulse product vision

## Problem

Teams can often count link clicks but cannot reliably connect campaign activity to meaningful outcomes. Data is fragmented across link tools, analytics systems, app backends, commerce systems, and spreadsheets. Click totals alone do not explain which campaigns create qualified leads, completed orders, enrolments, or settled transactions.

## Target users

- Growth and performance marketers who need trustworthy campaign reporting.
- Product and business analysts who investigate acquisition and conversion funnels.
- Small businesses and digital teams that need a self-hostable alternative to fragmented tools.
- Developers who need a simple, documented way to send business events.

## Product outcome

Give teams one transparent view from campaign touchpoint to verified business outcome, while allowing them to host and own their data.

## Differentiation hypotheses

1. Link management plus downstream business-event measurement in one system.
2. Transparent attribution rules and explicit evidence quality.
3. Self-hostable core with no mandatory SaaS subscription.
4. Industry-configurable event schemas rather than fixed vertical assumptions.
5. Privacy-conscious measurement without covert fingerprinting.

These are hypotheses to validate through user interviews and competitor testing, not proven market advantages.

## MVP boundaries

**In scope:** workspace/project model, link creation and redirects, UTM metadata, QR generation, click event collection, basic aggregation, API-key-authenticated business-event ingestion, simple funnel reporting, CSV export, Docker deployment.

**Out of scope initially:** payment processing, ad buying, CRM replacement, identity resolution across devices, covert fingerprinting, automatic access to private company systems, and claims of revenue attribution without verified conversion events.

## North-star metric

Share of tracked campaign journeys that can be connected to a valid, deduplicated downstream business event.

Supporting metrics: links created, valid clicks, bot-filtered events, event-ingestion success rate, conversion-event coverage, export completion, and self-hosted deployment success.

## Validation plan

- Interview 8–12 marketers, founders, and analysts across at least three industries.
- Ask users to demonstrate their current campaign-to-conversion reporting workflow.
- Test whether they need link management, event ingestion, attribution, or simply better exports.
- Validate privacy, hosting, and integration requirements before locking the MVP.
- Do not present illustrative company workflows as customer research.