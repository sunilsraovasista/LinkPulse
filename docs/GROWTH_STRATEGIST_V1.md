# LinkPulse Growth Strategist v1

## Purpose
Turn first-party LinkPulse click telemetry into a small set of transparent campaign investigation prompts.

## Implemented v1
- Deterministic rules, no external LLM provider or API key.
- Flags high bot/preview request share, missing referrer coverage, mobile-heavy device mix, referral-channel concentration, and material week-over-week click movement.
- Returns evidence, priority and suggested validation steps.
- Produces no recommendations when there is no click telemetry.

## API
`GET /api/strategy/growth` — returns recommendations based on the local click database.

## Explicit limitations
- This is a rules-based baseline, not an autonomous AI agent.
- Clicks are not conversions, qualified leads, customers or revenue.
- Device and referrer dimensions describe requests, not unique people.
- User-agent bot classification is heuristic.
- Conversion tracking, business-event ingestion and attribution are not yet implemented.
- The existing SQLite service is single-tenant development software; this endpoint must not be exposed publicly until authentication, workspace isolation and production controls are complete.

## Next gates
1. Complete authenticated workspaces and project-level data isolation.
2. Implement idempotent business-event ingestion and verified conversion events.
3. Add transparent funnels and attribution windows.
4. Add optional LLM explanations grounded in queryable evidence, with prompt-injection defenses and human approval.
5. Track accepted recommendations and verified campaign outcomes.
