import os
from pathlib import Path

from fastapi.testclient import TestClient

TEST_DB = Path(__file__).parent / "test-linkpulse.db"
os.environ["LINKPULSE_DB_PATH"] = str(TEST_DB)

from app.main import app, init_db  # noqa: E402

init_db()
client = TestClient(app)


def setup_function():
    with __import__("sqlite3").connect(TEST_DB) as conn:
        conn.execute("DELETE FROM clicks")
        conn.execute("DELETE FROM links")
        conn.commit()


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_and_redirect_records_click():
    created = client.post("/api/links", json={
        "destination_url": "https://example.com/welcome",
        "slug": "welcome1",
        "title": "Welcome campaign",
    })
    assert created.status_code == 201
    assert created.json()["short_path"] == "/r/welcome1"

    redirected = client.get("/r/welcome1", follow_redirects=False, headers={
        "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) Mobile",
        "referer": "https://newsletter.example.org/campaign",
    })
    assert redirected.status_code == 307
    assert redirected.headers["location"] == "https://example.com/welcome"

    analytics = client.get("/api/links/welcome1/analytics").json()
    assert analytics["total_clicks"] == 1
    assert analytics["devices"][0]["device_type"] == "mobile"
    assert analytics["referrers"][0]["source"] == "newsletter.example.org"


def test_update_rejects_null_destination_url():
    created = client.post("/api/links", json={
        "destination_url": "https://example.com/original",
        "slug": "nonnull1",
    })
    assert created.status_code == 201
    response = client.patch("/api/links/nonnull1", json={"destination_url": None})
    assert response.status_code == 422
    assert client.get("/api/links/nonnull1").json()["destination_url"] == "https://example.com/original"


def test_bot_preview_clicks_are_reported_separately():
    created = client.post("/api/links", json={
        "destination_url": "https://example.com",
        "slug": "botcheck1",
    })
    assert created.status_code == 201
    client.get("/r/botcheck1", follow_redirects=False, headers={"user-agent": "Slackbot-LinkExpanding"})
    client.get("/r/botcheck1", follow_redirects=False, headers={"user-agent": "Mozilla/5.0 (Windows NT 10.0) Chrome/120"})
    analytics = client.get("/api/links/botcheck1/analytics").json()
    assert analytics["total_clicks"] == 2
    assert analytics["human_clicks"] == 1
    assert analytics["bot_or_preview_clicks"] == 1
    overview = client.get("/api/analytics/overview").json()
    assert overview["tracked_clicks"] == 2
    assert overview["human_clicks"] == 1
    assert overview["bot_or_preview_clicks"] == 1


def test_utm_builder_preserves_existing_query_and_encodes_values():
    response = client.post("/api/utm/build", json={
        "destination_url": "https://example.com/pricing?plan=pro",
        "source": "linkedin",
        "medium": "paid social",
        "campaign": "november_launch",
        "content": "founder story & demo",
    })
    assert response.status_code == 200
    result = response.json()
    assert "plan=pro" in result["tagged_url"]
    assert "utm_source=linkedin" in result["tagged_url"]
    assert "utm_medium=paid+social" in result["tagged_url"]
    assert "utm_content=founder+story+%26+demo" in result["tagged_url"]


def test_duplicate_slug_is_conflict():
    body = {"destination_url": "https://example.com", "slug": "same-slug"}
    assert client.post("/api/links", json=body).status_code == 201
    assert client.post("/api/links", json=body).status_code == 409


def test_rejects_non_http_destination():
    response = client.post("/api/links", json={"destination_url": "javascript:alert(1)"})
    assert response.status_code == 422


def test_unknown_slug_is_404():
    assert client.get("/r/not-found").status_code == 404


def test_link_can_be_updated_and_archived():
    created = client.post("/api/links", json={
        "destination_url": "https://example.com/start",
        "slug": "lifecycle1",
    })
    assert created.status_code == 201

    updated = client.patch("/api/links/lifecycle1", json={
        "title": "Updated campaign",
        "destination_url": "https://example.com/new",
    })
    assert updated.status_code == 200
    assert updated.json()["title"] == "Updated campaign"
    assert updated.json()["destination_url"] == "https://example.com/new"

    archived = client.delete("/api/links/lifecycle1")
    assert archived.status_code == 204
    assert client.get("/r/lifecycle1").status_code == 404


def test_expired_link_returns_gone():
    created = client.post("/api/links", json={
        "destination_url": "https://example.com",
        "slug": "expired1",
        "expires_at": "2020-01-01T00:00:00Z",
    })
    assert created.status_code == 201
    assert client.get("/r/expired1").status_code == 410


def test_click_limit_stops_redirecting_after_limit():
    created = client.post("/api/links", json={
        "destination_url": "https://example.com",
        "slug": "limited1",
        "max_clicks": 1,
    })
    assert created.status_code == 201
    assert client.get("/r/limited1", follow_redirects=False).status_code == 307
    assert client.get("/r/limited1", follow_redirects=False).status_code == 410


def test_expiry_requires_timezone():
    response = client.post("/api/links", json={
        "destination_url": "https://example.com",
        "slug": "badexpiry",
        "expires_at": "2030-01-01T00:00:00",
    })
    assert response.status_code == 422


def test_qr_endpoint_returns_png_for_active_link():
    created = client.post("/api/links", json={
        "destination_url": "https://example.com",
        "slug": "qrcode1",
    })
    assert created.status_code == 201
    response = client.get("/api/links/qrcode1/qr")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG\r\n\x1a\n")


def test_qr_endpoint_rejects_archived_link():
    client.post("/api/links", json={
        "destination_url": "https://example.com",
        "slug": "qrarchive1",
    })
    client.delete("/api/links/qrarchive1")
    assert client.get("/api/links/qrarchive1/qr").status_code == 410


def test_dashboard_is_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "Campaign workspace" in response.text
    assert "Create a short link" in response.text
    assert 'title="Open PNG QR code"' in response.text


def test_production_qr_requires_canonical_public_base_url(monkeypatch):
    client.post("/api/links", json={
        "destination_url": "https://example.com",
        "slug": "prodqr001",
    })
    monkeypatch.setenv("LINKPULSE_ENV", "production")
    monkeypatch.delenv("LINKPULSE_PUBLIC_BASE_URL", raising=False)
    response = client.get(
        "/api/links/prodqr001/qr",
        headers={"host": "attacker.example"},
    )
    assert response.status_code == 503
    assert "LINKPULSE_PUBLIC_BASE_URL" in response.json()["detail"]


def test_qr_uses_configured_canonical_public_base_url(monkeypatch):
    client.post("/api/links", json={
        "destination_url": "https://example.com",
        "slug": "canonical1",
    })
    monkeypatch.setenv("LINKPULSE_ENV", "production")
    monkeypatch.setenv("LINKPULSE_PUBLIC_BASE_URL", "https://go.example.org")
    response = client.get(
        "/api/links/canonical1/qr",
        headers={"host": "attacker.example"},
    )
    assert response.status_code == 200
    from PIL import Image
    import io
    qr = Image.open(io.BytesIO(response.content))
    assert qr.format == "PNG"
    monkeypatch.delenv("LINKPULSE_ENV", raising=False)
    monkeypatch.delenv("LINKPULSE_PUBLIC_BASE_URL", raising=False)


def test_qr_rejects_invalid_configured_public_base_url(monkeypatch):
    client.post("/api/links", json={
        "destination_url": "https://example.com",
        "slug": "badbase001",
    })
    monkeypatch.setenv("LINKPULSE_PUBLIC_BASE_URL", "javascript:alert(1)")
    response = client.get("/api/links/badbase001/qr")
    assert response.status_code == 500



def test_production_startup_fails_closed_until_security_foundation(monkeypatch):
    import pytest

    monkeypatch.setenv("LINKPULSE_ENV", "production")
    with pytest.raises(RuntimeError, match="Production startup is disabled"):
        with TestClient(app):
            pass
