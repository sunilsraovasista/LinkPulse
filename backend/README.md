# LinkPulse API — first working slice

This service implements a first local development slice:

- Create a short link with an optional custom slug.
- Update destinations/titles, archive links, and enforce optional expiry timestamps or click limits.
- Redirect through `/r/{slug}`.
- Record click timestamp, referrer host and coarse device class.
- Inspect per-link analytics and workspace overview, with bot/link-preview requests counted separately from human-classified requests.
- Build UTM-tagged campaign URLs while preserving existing destination query parameters (`POST /api/utm/build`).
- Generate PNG QR codes for active short links (`GET /api/links/{slug}/qr`).
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

For deployments behind a proxy or custom domain, set `LINKPULSE_PUBLIC_BASE_URL` to the canonical public base URL (for example, `https://go.example.com`). Set `LINKPULSE_ENV=production` in production: QR generation then fails closed with HTTP 503 unless the canonical URL is configured, rather than trusting the request `Host` header. The configured value must use HTTP(S) and must not contain credentials, a query, or a fragment. In development only, the request origin remains the fallback.

## Run with Docker

From the repository root:

```bash
docker compose up --build
```

## Important limitations

This is a development slice, not a production deployment. It uses SQLite, has no user authentication or workspace isolation, and does not yet support custom-domain DNS verification, advanced bot filtering, consent management, retention jobs, business-event attribution, or authentication/workspace isolation. `LINKPULSE_ENV=production` currently makes application startup fail closed because this build is not safe for public multi-tenant use. Do not remove this guard until authentication, workspace/project scoping, PostgreSQL migrations, rate limits, and the production security review are complete. The UTM builder is API-only and is not yet available in the dashboard. Do not expose it publicly with real customer data until those controls are implemented and reviewed.
