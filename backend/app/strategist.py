"""Transparent rules-based growth recommendations from LinkPulse click telemetry."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any


def build_growth_strategy(metrics: dict[str, Any], today: date | None = None) -> dict[str, Any]:
    """Generate bounded recommendations; clicks are never represented as conversions."""
    today = today or datetime.now(timezone.utc).date()
    total = int(metrics.get("total_clicks", 0))
    human = int(metrics.get("human_clicks", 0))
    bot = int(metrics.get("bot_or_preview_clicks", 0))
    devices = {str(x["device_type"]): int(x["clicks"]) for x in metrics.get("devices", [])}
    referrers = {str(x["source"]): int(x["clicks"]) for x in metrics.get("referrers", [])}
    daily = {date.fromisoformat(str(x["day"])): int(x["clicks"]) for x in metrics.get("daily_clicks", [])}

    recommendations: list[dict[str, Any]] = []

    def add(key: str, title: str, priority: str, evidence: str, action: str, count: int | None = None) -> None:
        recommendations.append({
            "id": key,
            "title": title,
            "priority": priority,
            "evidence": evidence,
            "recommended_action": action,
            "evidence_count": count,
            "requires_human_validation": True,
        })

    if total == 0:
        return {
            "status": "insufficient_data",
            "strategy_version": "rules-v1",
            "method": "deterministic_rules",
            "summary": {"total_clicks": 0, "human_clicks": 0, "bot_or_preview_clicks": 0},
            "recommendations": [],
            "guardrails": [
                "No click data is available; no growth recommendation is generated.",
                "Clicks are not conversions, customers or revenue.",
            ],
        }

    bot_share = bot / total
    if bot_share >= 0.25:
        add(
            "bot-preview-share",
            "Separate automated previews from campaign performance",
            "high" if bot_share >= 0.5 else "medium",
            f"{bot} of {total} tracked requests ({bot_share:.0%}) were classified as bot or preview traffic.",
            "Review the user-agent classification and report human-classified and bot/preview traffic separately; do not treat either as unique people.",
            bot,
        )

    direct = referrers.get("direct / unknown", 0)
    if human and direct / max(human, 1) >= 0.4:
        add(
            "attribution-coverage",
            "Improve campaign source tagging",
            "medium",
            f"{direct} requests have no recorded referrer host.",
            "Use consistent UTM parameters and preserve campaign identifiers through the destination journey. Referrer absence does not prove a direct visit.",
            direct,
        )

    mobile = devices.get("mobile", 0)
    tablet = devices.get("tablet", 0)
    known_device = sum(devices.values()) - devices.get("desktop_or_unknown", 0) - devices.get("bot_or_preview", 0)
    mobile_share = (mobile + tablet) / max(known_device, 1)
    if known_device >= 10 and mobile_share >= 0.65:
        add(
            "mobile-experience",
            "Prioritise a mobile landing-page review",
            "medium",
            f"{mobile + tablet} of {known_device} classifiable device requests ({mobile_share:.0%}) were mobile or tablet.",
            "Test the destination page on common mobile screen sizes, check load performance and validate the primary call to action.",
            mobile + tablet,
        )

    source_total = sum(referrers.values())
    if source_total >= 10 and referrers:
        source, source_clicks = max(referrers.items(), key=lambda item: item[1])
        concentration = source_clicks / source_total
        if source != "direct / unknown" and concentration >= 0.7:
            add(
                "channel-concentration",
                "Validate dependence on the leading referral channel",
                "medium",
                f"{source} accounts for {source_clicks} of {source_total} requests with a recorded referrer ({concentration:.0%}).",
                "Compare campaign objectives and downstream outcomes across at least one additional channel before reallocating budget.",
                source_clicks,
            )

    current_days = [today - timedelta(days=i) for i in range(7)]
    previous_days = [today - timedelta(days=i) for i in range(7, 14)]
    current = sum(daily.get(day, 0) for day in current_days)
    previous = sum(daily.get(day, 0) for day in previous_days)
    if previous >= 10:
        change = (current - previous) / previous
        if change <= -0.25:
            add(
                "click-decline",
                "Investigate the recent click decline",
                "high" if change <= -0.5 else "medium",
                f"Tracked clicks changed from {previous} in the previous 7 days to {current} in the latest 7 days ({change:.0%}).",
                "Check link status, campaign schedules, destination availability and channel activity before attributing the decline to a specific cause.",
                current,
            )
        elif change >= 0.5:
            add(
                "click-growth",
                "Validate the recent increase before scaling",
                "low",
                f"Tracked clicks changed from {previous} in the previous 7 days to {current} in the latest 7 days ({change:.0%}).",
                "Confirm the increase is not driven by previews, bots or duplicate traffic, then compare verified downstream business events.",
                current,
            )

    rank = {"high": 0, "medium": 1, "low": 2}
    recommendations.sort(key=lambda item: (rank[item["priority"]], item["id"]))
    return {
        "status": "ready" if recommendations else "no_actionable_signal",
        "strategy_version": "rules-v1",
        "method": "deterministic_rules",
        "summary": {
            "total_clicks": total,
            "human_clicks": human,
            "bot_or_preview_clicks": bot,
            "recorded_referrer_sources": len(referrers),
            "classifiable_device_requests": known_device,
            "latest_7_day_clicks": current,
            "previous_7_day_clicks": previous,
        },
        "recommendations": recommendations,
        "guardrails": [
            "This is a deterministic recommendation baseline, not an LLM-powered strategist.",
            "A click is not a conversion, qualified lead, customer or revenue event.",
            "User-agent bot classification is heuristic and may misclassify traffic.",
            "Referrer absence does not prove a direct visit; browser privacy and app hand-offs can remove referrers.",
            "Device and source shares describe recorded requests, not unique people.",
            "Recommendations are investigation prompts; validate them before changing campaign budgets.",
        ],
    }
