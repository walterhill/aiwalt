"""
Data models for shipments, milestones, exceptions, and references.

Plain dataclasses — no ORM, no database dependency.
Designed to be populated from any source: seed data, CSV, API, flat file.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class ReferenceNumbers:
    """All reference numbers associated with a shipment."""
    po: str = ""
    asn: str = ""
    container: str = ""
    bol: str = ""
    pro: str = ""

    def as_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v}


@dataclass
class Milestone:
    """A single event in the shipment lifecycle."""
    event: str
    timestamp: datetime
    location: str = ""
    source: str = ""  # e.g. "Carrier EDI", "Vendor Portal", "Manual"

    def as_dict(self) -> dict:
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        return d


@dataclass
class Exception:
    """A detected exception on a shipment."""
    type: str          # "late", "stale", "at_risk"
    severity: int      # Higher = more urgent
    reason: str        # Human-readable explanation
    data: dict = field(default_factory=dict)  # Supporting evidence

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class Shipment:
    """A single inbound shipment."""
    shipment_id: str
    vendor: str
    mode: str                          # Ocean, Air, Truck, Rail
    origin: str
    destination: str
    planned_eta: datetime
    current_eta: datetime
    status: str                        # Booked, In Transit, At Port, Delivered, etc.
    references: ReferenceNumbers = field(default_factory=ReferenceNumbers)
    milestones: list[Milestone] = field(default_factory=list)
    exceptions: list[Exception] = field(default_factory=list)
    last_update: Optional[datetime] = None

    @property
    def severity_score(self) -> int:
        """Total severity across all exceptions. Used for dashboard sort."""
        return sum(e.severity for e in self.exceptions)

    @property
    def has_exceptions(self) -> bool:
        return len(self.exceptions) > 0

    @property
    def exception_types(self) -> list[str]:
        return sorted(set(e.type for e in self.exceptions))

    @property
    def eta_slip_hours(self) -> float:
        """How many hours the current ETA has slipped beyond planned."""
        delta = (self.current_eta - self.planned_eta).total_seconds() / 3600
        return max(0.0, delta)

    def as_dict(self) -> dict:
        d = {
            "shipment_id": self.shipment_id,
            "vendor": self.vendor,
            "mode": self.mode,
            "origin": self.origin,
            "destination": self.destination,
            "planned_eta": self.planned_eta.isoformat(),
            "current_eta": self.current_eta.isoformat(),
            "status": self.status,
            "references": self.references.as_dict(),
            "milestones": [m.as_dict() for m in self.milestones],
            "exceptions": [e.as_dict() for e in self.exceptions],
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "severity_score": self.severity_score,
            "has_exceptions": self.has_exceptions,
            "exception_types": self.exception_types,
            "eta_slip_hours": round(self.eta_slip_hours, 1),
        }
        return d

    def as_json(self) -> str:
        return json.dumps(self.as_dict(), indent=2)
