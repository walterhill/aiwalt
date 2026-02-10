"""
Pseudo data generator for MVP browser testing.

Generates realistic inbound shipments with varied statuses, modes,
vendors, and timelines. Designed to exercise all exception paths
so the dashboard has meaningful content on first load.

In production, this module would be replaced by real data ingestion
from CSV uploads, ERP exports, flat files, or carrier APIs.
"""

from datetime import datetime, timedelta, timezone
import random

from models import Shipment, ReferenceNumbers, Milestone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --- Lookup Data ---

VENDORS = [
    "Shenzhen Precision Parts Co.",
    "Hamburg Industrial Supply GmbH",
    "São Paulo Components Ltda.",
    "Chennai Manufacturing Pvt. Ltd.",
    "Yokohama Electronics Corp.",
    "Istanbul Textiles A.Ş.",
    "Rotterdam Bulk Materials BV",
    "Busan Chemical Industries",
    "Melbourne Agricultural Exports",
    "Guadalajara Auto Parts S.A.",
    "Taipei Semiconductor Ltd.",
    "Ho Chi Minh Packaging Co.",
]

ORIGINS = [
    ("Shenzhen, CN", "Ocean"),
    ("Hamburg, DE", "Ocean"),
    ("São Paulo, BR", "Air"),
    ("Chennai, IN", "Ocean"),
    ("Yokohama, JP", "Ocean"),
    ("Istanbul, TR", "Air"),
    ("Rotterdam, NL", "Truck"),
    ("Busan, KR", "Ocean"),
    ("Melbourne, AU", "Air"),
    ("Guadalajara, MX", "Truck"),
    ("Taipei, TW", "Air"),
    ("Ho Chi Minh City, VN", "Ocean"),
    ("Chicago, US", "Rail"),
    ("Dallas, US", "Truck"),
    ("Memphis, US", "Rail"),
]

DESTINATIONS = [
    "Chicago, IL DC",
    "Los Angeles, CA DC",
    "Newark, NJ DC",
    "Savannah, GA DC",
    "Houston, TX DC",
    "Seattle, WA DC",
]

STATUSES = [
    "Booked",
    "Picked Up",
    "In Transit",
    "At Port",
    "Customs Hold",
    "Out for Delivery",
    "Delivered",
]


def _random_refs(idx: int) -> ReferenceNumbers:
    return ReferenceNumbers(
        po=f"PO-2025-{10000 + idx}",
        asn=f"ASN-{20000 + idx}" if random.random() > 0.3 else "",
        container=f"CONT{random.choice('ABCDEF')}{random.randint(1000000, 9999999)}" if random.random() > 0.4 else "",
        bol=f"BOL-{random.randint(100000, 999999)}",
        pro=f"PRO-{random.randint(10000, 99999)}" if random.random() > 0.5 else "",
    )


def _generate_milestones(
    mode: str,
    origin: str,
    destination: str,
    start: datetime,
    status: str,
) -> list[Milestone]:
    """Generate a realistic milestone timeline based on mode and status."""
    milestones = []
    t = start
    sources = ["Vendor Portal", "Carrier EDI", "Port System", "Manual Entry"]

    # Booking
    milestones.append(Milestone(
        event="Booking Confirmed",
        timestamp=t,
        location=origin,
        source="Vendor Portal",
    ))

    if status == "Booked":
        return milestones

    # Pickup
    t += timedelta(hours=random.randint(12, 72))
    milestones.append(Milestone(
        event="Picked Up",
        timestamp=t,
        location=origin,
        source=random.choice(sources),
    ))

    if status == "Picked Up":
        return milestones

    # Departure
    t += timedelta(hours=random.randint(4, 24))
    if mode == "Ocean":
        milestones.append(Milestone(
            event="Vessel Departed",
            timestamp=t,
            location=origin,
            source="Carrier EDI",
        ))
    elif mode == "Air":
        milestones.append(Milestone(
            event="Flight Departed",
            timestamp=t,
            location=origin,
            source="Carrier EDI",
        ))
    else:
        milestones.append(Milestone(
            event="Departed Origin",
            timestamp=t,
            location=origin,
            source="Carrier EDI",
        ))

    if status == "In Transit":
        # Maybe add an in-transit update
        if random.random() > 0.4:
            t += timedelta(hours=random.randint(24, 120))
            milestones.append(Milestone(
                event="In Transit Update",
                timestamp=t,
                location="En Route",
                source="Carrier EDI",
            ))
        return milestones

    # Arrival
    if mode in ("Ocean", "Air"):
        t += timedelta(hours=random.randint(48, 480))
        milestones.append(Milestone(
            event="Arrived at Port" if mode == "Ocean" else "Arrived at Airport",
            timestamp=t,
            location=destination,
            source="Port System",
        ))

    if status == "At Port":
        return milestones

    # Customs
    if status in ("Customs Hold", "Out for Delivery", "Delivered"):
        t += timedelta(hours=random.randint(2, 48))
        milestones.append(Milestone(
            event="Customs Cleared" if status != "Customs Hold" else "Customs Hold",
            timestamp=t,
            location=destination,
            source="Port System",
        ))

    if status == "Customs Hold":
        return milestones

    # Out for delivery
    t += timedelta(hours=random.randint(4, 24))
    milestones.append(Milestone(
        event="Out for Delivery",
        timestamp=t,
        location=destination,
        source="Carrier EDI",
    ))

    if status == "Out for Delivery":
        return milestones

    # Delivered
    t += timedelta(hours=random.randint(2, 8))
    milestones.append(Milestone(
        event="Delivered",
        timestamp=t,
        location=destination,
        source="Manual Entry",
    ))

    return milestones


def generate_shipments(count: int = 40) -> list[Shipment]:
    """
    Generate a set of pseudo shipments designed to cover all exception
    scenarios and status combinations.

    Distribution is intentionally weighted toward non-delivered shipments
    so the dashboard has plenty to show.
    """
    now = _utcnow()
    shipments = []

    for i in range(count):
        origin_entry = random.choice(ORIGINS)
        origin = origin_entry[0]
        mode = origin_entry[1]
        destination = random.choice(DESTINATIONS)
        vendor = random.choice(VENDORS)

        # Weight toward in-transit and exception-prone statuses
        if i < 8:
            status = "In Transit"
        elif i < 14:
            status = "At Port"
        elif i < 18:
            status = "Booked"
        elif i < 22:
            status = "Customs Hold"
        elif i < 26:
            status = "Picked Up"
        elif i < 30:
            status = "Out for Delivery"
        else:
            status = "Delivered"

        # Plan the ETAs to create varied exception scenarios
        if i < 5:
            # Late shipments: ETA slipped significantly
            planned_eta = now - timedelta(days=random.randint(2, 8))
            current_eta = now + timedelta(days=random.randint(1, 5))
            booking_start = now - timedelta(days=random.randint(20, 40))
            last_update = now - timedelta(hours=random.randint(1, 36))
        elif i < 10:
            # Stale shipments: no update for a long time
            planned_eta = now + timedelta(days=random.randint(3, 15))
            current_eta = now + timedelta(days=random.randint(3, 15))
            booking_start = now - timedelta(days=random.randint(15, 30))
            last_update = now - timedelta(hours=random.randint(50, 200))
        elif i < 16:
            # At-risk: arriving soon, not delivered
            planned_eta = now + timedelta(days=random.uniform(0.5, 2.5))
            current_eta = now + timedelta(days=random.uniform(0.5, 2.5))
            booking_start = now - timedelta(days=random.randint(10, 25))
            last_update = now - timedelta(hours=random.randint(1, 24))
        elif i < 22:
            # Mixed: some late + stale
            slip = random.randint(1, 6)
            planned_eta = now + timedelta(days=random.randint(2, 10))
            current_eta = planned_eta + timedelta(days=slip)
            booking_start = now - timedelta(days=random.randint(10, 30))
            last_update = now - timedelta(hours=random.randint(40, 100))
        else:
            # Clean shipments: on time, recently updated
            planned_eta = now + timedelta(days=random.randint(5, 30))
            current_eta = planned_eta + timedelta(hours=random.randint(-12, 12))
            booking_start = now - timedelta(days=random.randint(5, 20))
            last_update = now - timedelta(hours=random.randint(1, 20))

        milestones = _generate_milestones(mode, origin, destination, booking_start, status)

        shipment = Shipment(
            shipment_id=f"SHP-{2025}{i+1:04d}",
            vendor=vendor,
            mode=mode,
            origin=origin,
            destination=destination,
            planned_eta=planned_eta,
            current_eta=current_eta,
            status=status,
            references=_random_refs(i),
            milestones=milestones,
            last_update=last_update,
        )
        shipments.append(shipment)

    return shipments
