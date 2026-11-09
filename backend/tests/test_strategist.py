from datetime import date, timedelta

from app.strategist import build_growth_strategy


def test_empty_telemetry_does_not_invent_recommendations():
    result = build_growth_strategy({"total_clicks": 0})
    assert result["status"] == "insufficient_data"
    assert result["recommendations"] == []


def test_bot_share_and_unknown_referrer_generate_evidence_backed_actions():
    result = build_growth_strategy({
        "total_clicks": 100,
        "human_clicks": 55,
        "bot_or_preview_clicks": 45,
        "devices": [{"device_type": "mobile", "clicks": 30}, {"device_type": "desktop_or_unknown", "clicks": 25}],
        "referrers": [{"source": "direct / unknown", "clicks": 30}, {"source": "newsletter.example", "clicks": 25}],
        "daily_clicks": [],
    })
    ids = {item["id"] for item in result["recommendations"]}
    assert "bot-preview-share" in ids
    assert "attribution-coverage" in ids
    assert all(item["requires_human_validation"] for item in result["recommendations"])


def test_recent_click_decline_is_compared_over_two_seven_day_windows():
    today = date(2026, 11, 9)
    daily = []
    for offset in range(14):
        day = today - timedelta(days=offset)
        daily.append({"day": day.isoformat(), "clicks": 2 if offset < 7 else 10})
    result = build_growth_strategy({
        "total_clicks": 84,
        "human_clicks": 80,
        "bot_or_preview_clicks": 4,
        "devices": [{"device_type": "desktop_or_unknown", "clicks": 80}],
        "referrers": [{"source": "linkedin.example", "clicks": 80}],
        "daily_clicks": daily,
    }, today=today)
    decline = next(item for item in result["recommendations"] if item["id"] == "click-decline")
    assert decline["priority"] == "high"
    assert "80" in decline["evidence"]
    assert "16" in decline["evidence"]


def test_clicks_are_never_described_as_conversions_or_revenue():
    result = build_growth_strategy({
        "total_clicks": 3,
        "human_clicks": 3,
        "bot_or_preview_clicks": 0,
        "devices": [],
        "referrers": [],
        "daily_clicks": [],
    })
    assert any("not a conversion" in item.lower() for item in result["guardrails"])
