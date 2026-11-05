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


def test_duplicate_slug_is_conflict():
    body = {"destination_url": "https://example.com", "slug": "same-slug"}
    assert client.post("/api/links", json=body).status_code == 201
    assert client.post("/api/links", json=body).status_code == 409


def test_rejects_non_http_destination():
    response = client.post("/api/links", json={"destination_url": "javascript:alert(1)"})
    assert response.status_code == 422


def test_unknown_slug_is_404():
    assert client.get("/r/not-found").status_code == 404
