# Security and privacy

## Reporting a vulnerability

Please do not publish exploitable vulnerability details in a public issue. Contact the repository maintainers privately through the GitHub profile and include reproduction steps, impact, and affected commit/version. A dedicated security contact will be added before a public production release.

## Data minimisation

LinkPulse is intended to measure campaign activity and business events, not to build covert identity profiles. The design should avoid covert fingerprinting and minimise personal data collection.

## Secrets

- Never commit API keys, credentials, private URLs, or production data.
- Store only hashed API-key material in persistent storage.
- Redact secrets and sensitive payload fields from logs.

## Responsible use

Operators are responsible for configuring lawful notices, consent, retention, and access controls for their deployments. This document is an initial project policy, not legal advice.

## Current status

The project is at initial scaffolding. A full threat model, security review, and vulnerability disclosure process must be completed before production use.