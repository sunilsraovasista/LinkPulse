# LinkPulse API — first working slice

This service implements a first local development slice:

- Create a short link with an optional custom slug.
- Update destinations/titles, archive links, and enforce optional expiry timestamps or click limits.
- Redirect through `/r/{slug}`.
- Record click timestamp, referrer host and coarse device class.
- Inspect per-link analytics and workspace overview, with bot/link-preview requests counted separately from human-classified requests.
- Build UTM-tagged campaign URLs while preserving existing destination query parameters (`POST /api/utm/build`).
- Persist data in SQLite for zero-configuration local use.

## Run locally

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for the interactive API.

## Run with Docker

From the repository root:

```bash
docker compose up --build
```

## Important limitations

This is a development slice, not a production deployment. It uses SQLite, has no user authentication or workspace isolation, and does not yet support custom-domain DNS verification, QR generation, advanced bot filtering, consent management, retention jobs, business-event attribution, or authentication/workspace isolation. The UTM builder is API-only and is not yet available in the dashboard. Do not expose it publicly with real customer data until those controls are implemented and reviewed.
