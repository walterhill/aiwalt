"""
Exception detection engine.

Evaluates each shipment against configurable thresholds and attaches
exception flags with severity scores and human-readable reasons.

This is the core logic that powers the "exception-first" dashboard.
"""

from datetime import datetime, timezone

from models import Shipment, Exception
from config import (
    LATE_THRESHOLD_HOURS,
    STALE_THRESHOLD_HOURS,
    AT_RISK_DAYS,
    SEVERITY_WEIGHTS,
    LATE_SEVERITY_PER_DAY,
    STALE_SEVERITY_PER_DAY,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def check_late(shipment: Shipment) -> Exception | None:
    """Flag if current ETA has slipped beyond planned ETA by more than threshold."""
    slip_hours = shipment.eta_slip_hours
    if slip_hours <= LATE_THRESHOLD_HOURS:
        return None

    slip_days = slip_hours / 24
    severity = SEVERITY_WEIGHTS["late"] + int(slip_days) * LATE_SEVERITY_PER_DAY
    reason = (
        f"ETA slipped {slip_hours:.0f} hours ({slip_days:.1f} days) "
        f"beyond planned arrival. "
        f"Planned: {shipment.planned_eta.strftime('%Y-%m-%d %H:%M')}. "
        f"Current: {shipment.current_eta.strftime('%Y-%m-%d %H:%M')}."
    )
    return Exception(
        type="late",
        severity=severity,
        reason=reason,
        data={
            "slip_hours": round(slip_hours, 1),
            "slip_days": round(slip_days, 1),
            "planned_eta": shipment.planned_eta.isoformat(),
            "current_eta": shipment.current_eta.isoformat(),
            "threshold_hours": LATE_THRESHOLD_HOURS,
        },
    )


def check_stale(shipment: Shipment) -> Exception | None:
    """Flag if no update has been received beyond the stale window."""
    if shipment.status == "Delivered":
        return None

    if shipment.last_update is None:
        # No update ever — treat as stale from shipment creation
        hours_since = 999
    else:
        last = shipment.last_update
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        hours_since = (_now() - last).total_seconds() / 3600

    if hours_since <= STALE_THRESHOLD_HOURS:
        return None

    extra_hours = hours_since - STALE_THRESHOLD_HOURS
    extra_days = extra_hours / 24
    severity = SEVERITY_WEIGHTS["stale"] + int(extra_days) * STALE_SEVERITY_PER_DAY
    reason = (
        f"No tracking update in {hours_since:.0f} hours "
        f"(threshold: {STALE_THRESHOLD_HOURS}h). "
        f"Last update: {shipment.last_update.strftime('%Y-%m-%d %H:%M') if shipment.last_update else 'never'}."
    )
    return Exception(
        type="stale",
        severity=severity,
        reason=reason,
        data={
            "hours_since_update": round(hours_since, 1),
            "threshold_hours": STALE_THRESHOLD_HOURS,
            "last_update": shipment.last_update.isoformat() if shipment.last_update else None,
        },
    )


def check_at_risk(shipment: Shipment) -> Exception | None:
    """Flag if ETA is within the at-risk window and not yet delivered."""
    if shipment.status == "Delivered":
        return None

    now = _now()
    eta = shipment.current_eta
    if eta.tzinfo is None:
        eta = eta.replace(tzinfo=timezone.utc)

    days_until = (eta - now).total_seconds() / 86400

    if days_until < 0 or days_until > AT_RISK_DAYS:
        return None

    severity = SEVERITY_WEIGHTS["at_risk"] + int(AT_RISK_DAYS - days_until) * 5
    reason = (
        f"ETA is {days_until:.1f} days away and status is '{shipment.status}'. "
        f"Arriving within the {AT_RISK_DAYS}-day watch window."
    )
    return Exception(
        type="at_risk",
        severity=severity,
        reason=reason,
        data={
            "days_until_eta": round(days_until, 1),
            "threshold_days": AT_RISK_DAYS,
            "current_status": shipment.status,
        },
    )


def evaluate(shipment: Shipment) -> Shipment:
    """Run all exception checks and attach results to the shipment."""
    shipment.exceptions = []

    for checker in [check_late, check_stale, check_at_risk]:
        exc = checker(shipment)
        if exc is not None:
            shipment.exceptions.append(exc)

    # Sort exceptions by severity descending within the shipment.
    shipment.exceptions.sort(key=lambda e: e.severity, reverse=True)
    return shipment


def evaluate_all(shipments: list[Shipment]) -> list[Shipment]:
    """Evaluate exceptions on all shipments and return sorted by severity."""
    for s in shipments:
        evaluate(s)
    # Sort: shipments with exceptions first, then by severity score descending.
    shipments.sort(key=lambda s: s.severity_score, reverse=True)
    return shipments
