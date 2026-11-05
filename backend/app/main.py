from __future__ import annotations

import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator
from urllib.parse import urlparse
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field, HttpUrl, field_validator

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
        conn.execute("CREATE INDEX IF NOT EXISTS idx_clicks_link_time ON clicks(link_id, clicked_at)")


@app.on_event("startup")
def startup() -> None:
    init_db()


class LinkCreate(BaseModel):
    destination_url: HttpUrl
    slug: str | None = Field(default=None, min_length=3, max_length=48)
    title: str | None = Field(default=None, max_length=120)

    @field_validator("slug")
    @classmethod
    def valid_slug(cls, value: str | None) -> str | None:
        if value is not None and not SLUG_RE.fullmatch(value):
            raise ValueError("Slug must be 3-48 characters: letters, numbers, hyphens or underscores.")
        return value


class LinkOut(BaseModel):
    id: str
    slug: str
    destination_url: str
    title: str | None
    created_at: str
    is_active: bool
    short_path: str


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
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "linkpulse-api", "version": "0.1.0"}


@app.post("/api/links", response_model=LinkOut, status_code=201)
def create_link(payload: LinkCreate) -> dict:
    slug = payload.slug or uuid4().hex[:8]
    link_id = str(uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    with connection() as conn:
        try:
            conn.execute(
                "INSERT INTO links(id, slug, destination_url, title, created_at) VALUES (?, ?, ?, ?, ?)",
                (link_id, slug, str(payload.destination_url), payload.title, created_at),
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


@app.get("/r/{slug}")
def redirect_link(slug: str, request: Request) -> RedirectResponse:
    with connection() as conn:
        row = conn.execute(
            "SELECT * FROM links WHERE slug = ? AND is_active = 1", (slug,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Short link not found or inactive.")
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


@app.get("/api/links/{slug}/analytics")
def link_analytics(slug: str) -> dict:
    with connection() as conn:
        link = conn.execute("SELECT * FROM links WHERE slug = ?", (slug,)).fetchone()
        if link is None:
            raise HTTPException(status_code=404, detail="Short link not found.")
        total = conn.execute("SELECT COUNT(*) AS n FROM clicks WHERE link_id = ?", (link["id"],)).fetchone()["n"]
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
        recent = conn.execute(
            "SELECT l.slug, l.title, COUNT(c.id) AS clicks FROM links l "
            "LEFT JOIN clicks c ON c.link_id = l.id GROUP BY l.id ORDER BY clicks DESC LIMIT 10"
        ).fetchall()
    return {"active_links": link_count, "tracked_clicks": click_count, "top_links": [dict(row) for row in recent]}
