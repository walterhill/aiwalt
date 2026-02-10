"""
AI-powered features (feature-flagged).

These provide operator-friendly explanations grounded in structured
shipment data. No external API calls — all logic is rule-based for
the MVP. Designed to be replaced with LLM calls when ready.

All functions check config.AI_FEATURES_ENABLED and return None
when disabled.
"""

from models import Shipment
from config import AI_FEATURES_ENABLED


def explain_exceptions(shipment: Shipment) -> str | None:
    """
    Explain why a shipment is flagged, in plain operator language.
    Grounded in the shipment's exception data — never fabricates.
    """
    if not AI_FEATURES_ENABLED:
        return None

    if not shipment.exceptions:
        return "This shipment has no exceptions. It appears to be on track."

    lines = [f"Shipment {shipment.shipment_id} has {len(shipment.exceptions)} exception(s):\n"]

    for exc in shipment.exceptions:
        if exc.type == "late":
            days = exc.data.get("slip_days", 0)
            lines.append(
                f"- LATE: The ETA has slipped by {days} days. "
                f"Originally expected {exc.data.get('planned_eta', 'N/A')}, "
                f"now expected {exc.data.get('current_eta', 'N/A')}. "
                f"This exceeds the {exc.data.get('threshold_hours', 24)}-hour threshold."
            )
        elif exc.type == "stale":
            hours = exc.data.get("hours_since_update", 0)
            lines.append(
                f"- STALE: No tracking update in {hours:.0f} hours. "
                f"The threshold is {exc.data.get('threshold_hours', 48)} hours. "
                f"Last known update: {exc.data.get('last_update', 'never')}."
            )
        elif exc.type == "at_risk":
            days = exc.data.get("days_until_eta", 0)
            lines.append(
                f"- AT RISK: ETA is {days:.1f} days away but status is "
                f"'{exc.data.get('current_status', 'unknown')}'. "
                f"This falls within the {exc.data.get('threshold_days', 3)}-day watch window."
            )

    return "\n".join(lines)


def summarize_changes(shipment: Shipment) -> str | None:
    """
    Summarize what has changed since the last update.
    In MVP, this describes the most recent milestone.
    """
    if not AI_FEATURES_ENABLED:
        return None

    if not shipment.milestones:
        return "No milestones recorded for this shipment."

    latest = shipment.milestones[-1]
    summary = (
        f"Most recent activity: '{latest.event}' "
        f"at {latest.location or 'unknown location'} "
        f"on {latest.timestamp.strftime('%Y-%m-%d %H:%M')} "
        f"(source: {latest.source or 'unknown'})."
    )

    if len(shipment.milestones) > 1:
        prev = shipment.milestones[-2]
        delta = latest.timestamp - prev.timestamp
        hours = delta.total_seconds() / 3600
        summary += (
            f" Previous event was '{prev.event}' "
            f"{hours:.0f} hours earlier."
        )

    if shipment.exceptions:
        types = ", ".join(e.type.upper() for e in shipment.exceptions)
        summary += f" Active exceptions: {types}."

    return summary


def draft_vendor_message(shipment: Shipment) -> str | None:
    """
    Draft a vendor follow-up message based on shipment exceptions.
    Grounded entirely in structured data.
    """
    if not AI_FEATURES_ENABLED:
        return None

    if not shipment.exceptions:
        return None

    lines = [
        f"Subject: Status Update Request — {shipment.shipment_id}\n",
        f"Hi {shipment.vendor} team,\n",
        f"We are tracking shipment {shipment.shipment_id} "
        f"(PO: {shipment.references.po or 'N/A'}) "
        f"and have identified the following concern(s):\n",
    ]

    for exc in shipment.exceptions:
        if exc.type == "late":
            lines.append(
                f"- The ETA has slipped from {exc.data.get('planned_eta', 'N/A')} "
                f"to {exc.data.get('current_eta', 'N/A')} "
                f"({exc.data.get('slip_days', '?')} days late)."
            )
        elif exc.type == "stale":
            lines.append(
                f"- We have not received a tracking update in "
                f"{exc.data.get('hours_since_update', '?'):.0f} hours."
            )
        elif exc.type == "at_risk":
            lines.append(
                f"- The shipment is due in {exc.data.get('days_until_eta', '?'):.1f} days "
                f"and the current status is '{exc.data.get('current_status', 'unknown')}'."
            )

    lines.extend([
        f"\nCould you please provide an updated status and revised ETA?",
        f"Shipment details:",
        f"  Mode: {shipment.mode}",
        f"  Origin: {shipment.origin}",
        f"  Destination: {shipment.destination}",
        f"  BOL: {shipment.references.bol or 'N/A'}",
        f"\nThank you.",
    ])

    return "\n".join(lines)
