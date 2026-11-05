from __future__ import annotations

import io
import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator
from urllib.parse import urlparse
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, RedirectResponse, Response
from pydantic import BaseModel, Field, HttpUrl, field_validator
import qrcode

DB_PATH = os.getenv("LINKPULSE_DB_PATH", str(Path(__file__).resolve().parents[1] / "linkpulse.db"))
SLUG_RE = re.compile(r"^[a-zA-Z0-9_-]{3,48}$")

app = FastAPI(
    title="LinkPulse API",
    version="0.1.0",
    description="Self-hostable link management and campaign measurement API.",
)


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS links (
                id TEXT PRIMARY KEY,
                slug TEXT NOT NULL UNIQUE,
                destination_url TEXT NOT NULL,
                title TEXT,
                created_at TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clicks (
                id TEXT PRIMARY KEY,
                link_id TEXT NOT NULL REFERENCES links(id),
                clicked_at TEXT NOT NULL,
                referrer_host TEXT,
                device_type TEXT NOT NULL
            )
        """)
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(links)").fetchall()}
        if "expires_at" not in columns:
            conn.execute("ALTER TABLE links ADD COLUMN expires_at TEXT")
        if "max_clicks" not in columns:
            conn.execute("ALTER TABLE links ADD COLUMN max_clicks INTEGER")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_clicks_link_time ON clicks(link_id, clicked_at)")


@app.on_event("startup")
def startup() -> None:
    init_db()


class UTMBuild(BaseModel):
    destination_url: HttpUrl
    source: str = Field(min_length=1, max_length=100)
    medium: str = Field(min_length=1, max_length=100)
    campaign: str = Field(min_length=1, max_length=150)
    term: str | None = Field(default=None, max_length=150)
    content: str | None = Field(default=None, max_length=150)


class LinkCreate(BaseModel):
    destination_url: HttpUrl
    slug: str | None = Field(default=None, min_length=3, max_length=48)
    title: str | None = Field(default=None, max_length=120)
    expires_at: datetime | None = None
    max_clicks: int | None = Field(default=None, ge=1, le=10000000)

    @field_validator("expires_at")
    @classmethod
    def timezone_required(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("expires_at must include a timezone.")
        return value

    @field_validator("slug")
    @classmethod
    def valid_slug(cls, value: str | None) -> str | None:
        if value is not None and not SLUG_RE.fullmatch(value):
            raise ValueError("Slug must be 3-48 characters: letters, numbers, hyphens or underscores.")
        return value


class LinkUpdate(BaseModel):
    destination_url: HttpUrl | None = None
    title: str | None = Field(default=None, max_length=120)
    is_active: bool | None = None
    expires_at: datetime | None = None
    max_clicks: int | None = Field(default=None, ge=1, le=10000000)

    @field_validator("destination_url")
    @classmethod
    def destination_cannot_be_null(cls, value: HttpUrl | None) -> HttpUrl:
        if value is None:
            raise ValueError("destination_url cannot be null.")
        return value

    @field_validator("expires_at")
    @classmethod
    def update_timezone_required(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("expires_at must include a timezone.")
        return value


class LinkOut(BaseModel):
    id: str
    slug: str
    destination_url: str
    title: str | None
    created_at: str
    is_active: bool
    short_path: str
    expires_at: str | None = None
    max_clicks: int | None = None


def classify_device(user_agent: str) -> str:
    ua = user_agent.lower()
    if any(token in ua for token in ("bot", "crawler", "spider", "preview", "facebookexternalhit", "slackbot")):
        return "bot_or_preview"
    if any(token in ua for token in ("ipad", "tablet")):
        return "tablet"
    if any(token in ua for token in ("mobile", "iphone", "android")):
        return "mobile"
    return "desktop_or_unknown"


def row_to_link(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "slug": row["slug"],
        "destination_url": row["destination_url"],
        "title": row["title"],
        "created_at": row["created_at"],
        "is_active": bool(row["is_active"]),
        "short_path": f"/r/{row['slug']}",
        "expires_at": row["expires_at"],
        "max_clicks": row["max_clicks"],
    }


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "linkpulse-api", "version": "0.1.0"}


@app.post("/api/utm/build")
def build_utm_url(payload: UTMBuild) -> dict:
    """Build a tagged URL while preserving existing destination query parameters."""
    from urllib.parse import parse_qsl, urlencode, urlunparse

    parsed = urlparse(str(payload.destination_url))
    utm_values = {
        "utm_source": payload.source,
        "utm_medium": payload.medium,
        "utm_campaign": payload.campaign,
    }
    if payload.term:
        utm_values["utm_term"] = payload.term
    if payload.content:
        utm_values["utm_content"] = payload.content
    # Preserve repeated non-UTM query keys (for example, repeated filter values).
    params = [
        (key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.startswith("utm_")
    ]
    params.extend(utm_values.items())
    tagged_url = urlunparse(parsed._replace(query=urlencode(params)))
    return {"tagged_url": tagged_url, "parameters": utm_values}


@app.post("/api/links", response_model=LinkOut, status_code=201)
def create_link(payload: LinkCreate) -> dict:
    slug = payload.slug or uuid4().hex[:8]
    link_id = str(uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    with connection() as conn:
        try:
            conn.execute(
                "INSERT INTO links(id, slug, destination_url, title, created_at, expires_at, max_clicks) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (link_id, slug, str(payload.destination_url), payload.title, created_at,
                 payload.expires_at.astimezone(timezone.utc).isoformat() if payload.expires_at else None,
                 payload.max_clicks),
            )
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="That short-link slug is already in use.")
        row = conn.execute("SELECT * FROM links WHERE id = ?", (link_id,)).fetchone()
    return row_to_link(row)


@app.get("/api/links", response_model=list[LinkOut])
def list_links() -> list[dict]:
    with connection() as conn:
        rows = conn.execute("SELECT * FROM links ORDER BY created_at DESC").fetchall()
    return [row_to_link(row) for row in rows]


@app.patch("/api/links/{slug}", response_model=LinkOut)
def update_link(slug: str, payload: LinkUpdate) -> dict:
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="Provide at least one field to update.")
    if "expires_at" in changes:
        value = changes["expires_at"]
        changes["expires_at"] = value.astimezone(timezone.utc).isoformat() if value else None
    if "destination_url" in changes and changes["destination_url"] is not None:
        changes["destination_url"] = str(changes["destination_url"])
    allowed = {"destination_url", "title", "is_active", "expires_at", "max_clicks"}
    assignments = ", ".join(f"{field} = ?" for field in changes if field in allowed)
    values = [value for field, value in changes.items() if field in allowed]
    with connection() as conn:
        existing = conn.execute("SELECT id FROM links WHERE slug = ?", (slug,)).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail="Short link not found.")
        conn.execute(f"UPDATE links SET {assignments} WHERE slug = ?", (*values, slug))
        row = conn.execute("SELECT * FROM links WHERE slug = ?", (slug,)).fetchone()
    return row_to_link(row)


@app.delete("/api/links/{slug}", status_code=204, response_class=Response)
def archive_link(slug: str) -> Response:
    with connection() as conn:
        result = conn.execute("UPDATE links SET is_active = 0 WHERE slug = ?", (slug,))
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Short link not found.")
    return Response(status_code=204)


@app.get("/r/{slug}")
def redirect_link(slug: str, request: Request) -> RedirectResponse:
    with connection() as conn:
        row = conn.execute(
            "SELECT * FROM links WHERE slug = ? AND is_active = 1", (slug,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Short link not found or inactive.")
        now = datetime.now(timezone.utc)
        if row["expires_at"] and datetime.fromisoformat(row["expires_at"]) <= now:
            raise HTTPException(status_code=410, detail="This short link has expired.")
        if row["max_clicks"] is not None:
            current_clicks = conn.execute(
                "SELECT COUNT(*) AS n FROM clicks WHERE link_id = ?", (row["id"],)
            ).fetchone()["n"]
            if current_clicks >= row["max_clicks"]:
                raise HTTPException(status_code=410, detail="This short link has reached its click limit.")
        referrer = request.headers.get("referer")
        referrer_host = urlparse(referrer).hostname if referrer else None
        device = classify_device(request.headers.get("user-agent", ""))
        # Store only a coarse device class and referrer host. No IP address or full user-agent.
        conn.execute(
            "INSERT INTO clicks(id, link_id, clicked_at, referrer_host, device_type) VALUES (?, ?, ?, ?, ?)",
            (str(uuid4()), row["id"], datetime.now(timezone.utc).isoformat(), referrer_host, device),
        )
        destination = row["destination_url"]
    return RedirectResponse(destination, status_code=307)


@app.get("/api/links/{slug}/qr")
def link_qr(slug: str, request: Request) -> Response:
    """Generate a PNG QR code for an active short link."""
    with connection() as conn:
        link = conn.execute(
            "SELECT slug, is_active FROM links WHERE slug = ?", (slug,)
        ).fetchone()
    if link is None:
        raise HTTPException(status_code=404, detail="Short link not found.")
    if not link["is_active"]:
        raise HTTPException(status_code=410, detail="Archived links do not have an active QR code.")
    configured_base = os.getenv("LINKPULSE_PUBLIC_BASE_URL")
    if not configured_base:
        # Host headers are request-controlled; use this fallback only in development.
        if os.getenv("LINKPULSE_ENV", "development").lower() == "production":
            raise HTTPException(status_code=503, detail="LINKPULSE_PUBLIC_BASE_URL must be configured in production.")
        public_base = str(request.base_url).rstrip("/")
    else:
        parsed_base = urlparse(configured_base)
        if (parsed_base.scheme not in {"http", "https"} or not parsed_base.hostname
                or parsed_base.username or parsed_base.password or parsed_base.query or parsed_base.fragment):
            raise HTTPException(status_code=500, detail="LINKPULSE_PUBLIC_BASE_URL must be an absolute HTTP(S) base URL without credentials, query, or fragment.")
        public_base = configured_base.rstrip("/")
    short_url = f"{public_base}/r/{slug}"
    image = qrcode.make(short_url)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return Response(
        content=buffer.getvalue(),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=300"},
    )


@app.get("/api/links/{slug}/analytics")
def link_analytics(slug: str) -> dict:
    with connection() as conn:
        link = conn.execute("SELECT * FROM links WHERE slug = ?", (slug,)).fetchone()
        if link is None:
            raise HTTPException(status_code=404, detail="Short link not found.")
        total = conn.execute("SELECT COUNT(*) AS n FROM clicks WHERE link_id = ?", (link["id"],)).fetchone()["n"]
        human_total = conn.execute(
            "SELECT COUNT(*) AS n FROM clicks WHERE link_id = ? AND device_type != 'bot_or_preview'",
            (link["id"],),
        ).fetchone()["n"]
        bot_total = total - human_total
        devices = conn.execute(
            "SELECT device_type, COUNT(*) AS clicks FROM clicks WHERE link_id = ? GROUP BY device_type ORDER BY clicks DESC",
            (link["id"],),
        ).fetchall()
        referrers = conn.execute(
            "SELECT COALESCE(referrer_host, 'direct / unknown') AS source, COUNT(*) AS clicks "
            "FROM clicks WHERE link_id = ? GROUP BY source ORDER BY clicks DESC LIMIT 20",
            (link["id"],),
        ).fetchall()
        daily = conn.execute(
            "SELECT substr(clicked_at, 1, 10) AS day, COUNT(*) AS clicks FROM clicks "
            "WHERE link_id = ? GROUP BY day ORDER BY day",
            (link["id"],),
        ).fetchall()
    return {
        "slug": slug,
        "total_clicks": total,
        "human_clicks": human_total,
        "bot_or_preview_clicks": bot_total,
        "devices": [dict(row) for row in devices],
        "referrers": [dict(row) for row in referrers],
        "daily_clicks": [dict(row) for row in daily],
        "measurement_note": "Raw IP addresses and full user-agent strings are not stored. Bot/preview traffic is classified but not excluded from totals yet.",
    }


@app.get("/api/analytics/overview")
def analytics_overview() -> dict:
    with connection() as conn:
        link_count = conn.execute("SELECT COUNT(*) AS n FROM links WHERE is_active = 1").fetchone()["n"]
        click_count = conn.execute("SELECT COUNT(*) AS n FROM clicks").fetchone()["n"]
        human_click_count = conn.execute(
            "SELECT COUNT(*) AS n FROM clicks WHERE device_type != 'bot_or_preview'"
        ).fetchone()["n"]
        bot_preview_count = click_count - human_click_count
        recent = conn.execute(
            "SELECT l.slug, l.title, COUNT(c.id) AS clicks FROM links l "
            "LEFT JOIN clicks c ON c.link_id = l.id GROUP BY l.id ORDER BY clicks DESC LIMIT 10"
        ).fetchall()
    return {
        "active_links": link_count,
        "tracked_clicks": click_count,
        "human_clicks": human_click_count,
        "bot_or_preview_clicks": bot_preview_count,
        "top_links": [dict(row) for row in recent],
    }
