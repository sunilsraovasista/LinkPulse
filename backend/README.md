# LinkPulse API — first working slice

This service implements a first local development slice:

- Create a short link with an optional custom slug.
- Update destinations/titles, archive links, and enforce optional expiry timestamps or click limits.
- Redirect through `/r/{slug}`.
- Record click timestamp, referrer host and coarse device class.
- Inspect per-link analytics and workspace overview.
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

This is a development slice, not a production deployment. It uses SQLite, has no user authentication or workspace isolation, and does not yet support custom-domain DNS verification, QR generation, bot exclusion, consent management, retention jobs, business-event attribution, or authentication/workspace isolation. Do not expose it publicly with real customer data until those controls are implemented and reviewed.
