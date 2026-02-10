"""
Pilot success metrics.

Tracks operational metrics that matter — not vanity numbers.
Designed to compare pre-pilot baselines with current performance.

For MVP, metrics are computed from the current shipment data set.
In production, these would be tracked over time in a simple store.
"""

from datetime import datetime, timezone

from models import Shipment
from config import PILOT_BASELINE


def compute_metrics(shipments: list[Shipment]) -> dict:
    """
    Compute current pilot metrics from the shipment data.

    Returns a dict with metric name, current value, baseline,
    and a simple direction indicator.
    """
    total = len(shipments)
    if total == 0:
        return {"shipments": 0, "metrics": []}

    # Count shipments with exceptions
    with_exceptions = sum(1 for s in shipments if s.has_exceptions)
    exception_rate = (with_exceptions / total) * 100

    # Count by exception type
    late_count = sum(1 for s in shipments for e in s.exceptions if e.type == "late")
    stale_count = sum(1 for s in shipments for e in s.exceptions if e.type == "stale")
    at_risk_count = sum(1 for s in shipments for e in s.exceptions if e.type == "at_risk")

    # Average severity score for flagged shipments
    flagged = [s for s in shipments if s.has_exceptions]
    avg_severity = (
        sum(s.severity_score for s in flagged) / len(flagged) if flagged else 0
    )

    # Estimate: how many minutes of manual reporting does this replace?
    # Assume each exception-flagged shipment would take ~3 minutes to
    # manually research and report on.
    estimated_reporting_saved_min = with_exceptions * 3

    # Estimate: how much earlier are delays detected?
    # For late shipments, the system flags them immediately on data load.
    # Baseline is manual detection which takes ~48 hours on average.
    baseline_detection_hours = PILOT_BASELINE["avg_delay_detection_hours"]
    current_detection_hours = 0.5  # Near-instant on data load

    # Status questions eliminated: each visible exception is a question
    # that doesn't need to be asked via email or Teams.
    status_questions_replaced = with_exceptions

    metrics = [
        {
            "name": "Reporting Time Eliminated",
            "description": "Estimated daily minutes saved by surfacing exceptions automatically",
            "current": f"{estimated_reporting_saved_min} min",
            "baseline": f"{PILOT_BASELINE['avg_reporting_minutes_per_day']} min",
            "direction": "down",
            "operational": True,
        },
        {
            "name": "Delay Detection Speed",
            "description": "How quickly delays are identified after they occur",
            "current": f"{current_detection_hours} hours",
            "baseline": f"{baseline_detection_hours} hours",
            "direction": "down",
            "operational": True,
        },
        {
            "name": "Status Questions Reduced",
            "description": "Inbound status questions replaced by self-service dashboard",
            "current": f"{status_questions_replaced} visible",
            "baseline": f"{PILOT_BASELINE['avg_status_questions_per_day']} / day",
            "direction": "down",
            "operational": True,
        },
        {
            "name": "Exception Coverage",
            "description": "Percentage of shipments evaluated for exceptions",
            "current": f"{total} / {total} (100%)",
            "baseline": "Manual spot-checks",
            "direction": "up",
            "operational": True,
        },
        {
            "name": "Shipments with Exceptions",
            "description": "How many shipments currently have at least one flag",
            "current": f"{with_exceptions} of {total} ({exception_rate:.0f}%)",
            "baseline": "Unknown (not tracked)",
            "direction": "neutral",
            "operational": True,
        },
        {
            "name": "Late Shipments",
            "description": "Shipments where ETA slipped beyond threshold",
            "current": str(late_count),
            "baseline": "Not tracked",
            "direction": "neutral",
            "operational": True,
        },
        {
            "name": "Stale Shipments",
            "description": "Shipments with no recent tracking update",
            "current": str(stale_count),
            "baseline": "Not tracked",
            "direction": "neutral",
            "operational": True,
        },
        {
            "name": "At-Risk Shipments",
            "description": "Shipments arriving soon that may need attention",
            "current": str(at_risk_count),
            "baseline": "Not tracked",
            "direction": "neutral",
            "operational": True,
        },
        {
            "name": "Average Severity Score",
            "description": "Average exception severity for flagged shipments",
            "current": f"{avg_severity:.1f}",
            "baseline": "N/A",
            "direction": "neutral",
            "operational": False,
        },
    ]

    return {
        "shipments_total": total,
        "shipments_with_exceptions": with_exceptions,
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
    }
