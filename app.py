"""
Inbound Logistics Visibility Platform — Flask Application.

Single source of truth for inbound shipments. Exception-first,
low-friction, operator-friendly.

Run with: python app.py
"""

import json
from flask import Flask, render_template, request, jsonify

from config import AI_FEATURES_ENABLED, PAGE_SIZE
from models import Shipment
from seed_data import generate_shipments
from exception_engine import evaluate_all
from ai_features import explain_exceptions, summarize_changes, draft_vendor_message
from metrics import compute_metrics

app = Flask(__name__)

# Generate and evaluate seed data on startup.
# In production, this would come from a data ingestion pipeline.
SHIPMENTS: list[Shipment] = evaluate_all(generate_shipments(40))

# Build a lookup dict for detail views.
SHIPMENT_MAP: dict[str, Shipment] = {s.shipment_id: s for s in SHIPMENTS}


def _filter_shipments(
    shipments: list[Shipment],
    search: str = "",
    mode: str = "",
    status: str = "",
    exception_type: str = "",
    exceptions_only: bool = False,
) -> list[Shipment]:
    """Filter shipments by search query, mode, status, and exception type."""
    results = shipments

    if search:
        q = search.lower()
        results = [
            s for s in results
            if q in s.shipment_id.lower()
            or q in s.vendor.lower()
            or q in s.origin.lower()
            or q in s.destination.lower()
            or q in s.references.po.lower()
            or q in s.references.asn.lower()
            or q in s.references.container.lower()
            or q in s.references.bol.lower()
            or q in s.references.pro.lower()
        ]

    if mode:
        results = [s for s in results if s.mode == mode]

    if status:
        results = [s for s in results if s.status == status]

    if exception_type:
        results = [
            s for s in results
            if any(e.type == exception_type for e in s.exceptions)
        ]

    if exceptions_only:
        results = [s for s in results if s.has_exceptions]

    return results


@app.route("/")
def dashboard():
    """Exception-first inbound dashboard — the default view."""
    search = request.args.get("search", "").strip()
    mode = request.args.get("mode", "")
    status = request.args.get("status", "")
    exception_type = request.args.get("exception_type", "")
    exceptions_only = request.args.get("exceptions_only", "") == "1"

    filtered = _filter_shipments(
        SHIPMENTS,
        search=search,
        mode=mode,
        status=status,
        exception_type=exception_type,
        exceptions_only=exceptions_only,
    )

    # Collect unique values for filter dropdowns.
    all_modes = sorted(set(s.mode for s in SHIPMENTS))
    all_statuses = sorted(set(s.status for s in SHIPMENTS))

    # Summary counts
    total = len(SHIPMENTS)
    total_exceptions = sum(1 for s in SHIPMENTS if s.has_exceptions)
    late_count = sum(1 for s in SHIPMENTS for e in s.exceptions if e.type == "late")
    stale_count = sum(1 for s in SHIPMENTS for e in s.exceptions if e.type == "stale")
    at_risk_count = sum(1 for s in SHIPMENTS for e in s.exceptions if e.type == "at_risk")

    return render_template(
        "dashboard.html",
        shipments=filtered,
        search=search,
        mode=mode,
        status=status,
        exception_type=exception_type,
        exceptions_only=exceptions_only,
        all_modes=all_modes,
        all_statuses=all_statuses,
        total=total,
        total_exceptions=total_exceptions,
        late_count=late_count,
        stale_count=stale_count,
        at_risk_count=at_risk_count,
        ai_enabled=AI_FEATURES_ENABLED,
    )


@app.route("/shipment/<shipment_id>")
def shipment_detail(shipment_id: str):
    """Drill-down detail view for a single shipment."""
    shipment = SHIPMENT_MAP.get(shipment_id)
    if shipment is None:
        return render_template("dashboard.html", error=f"Shipment {shipment_id} not found"), 404

    # AI features (will return None if disabled)
    ai_explanation = explain_exceptions(shipment)
    ai_summary = summarize_changes(shipment)
    ai_vendor_msg = draft_vendor_message(shipment)

    return render_template(
        "detail.html",
        s=shipment,
        raw_json=shipment.as_json(),
        ai_explanation=ai_explanation,
        ai_summary=ai_summary,
        ai_vendor_msg=ai_vendor_msg,
        ai_enabled=AI_FEATURES_ENABLED,
    )


@app.route("/metrics")
def metrics_page():
    """Pilot success metrics dashboard."""
    data = compute_metrics(SHIPMENTS)
    return render_template(
        "metrics.html",
        metrics_data=data,
        ai_enabled=AI_FEATURES_ENABLED,
    )


# --- JSON API (for transparency and future integrations) ---

@app.route("/api/shipments")
def api_shipments():
    """Return all shipments as JSON."""
    search = request.args.get("search", "").strip()
    mode = request.args.get("mode", "")
    status = request.args.get("status", "")
    exception_type = request.args.get("exception_type", "")
    exceptions_only = request.args.get("exceptions_only", "") == "1"

    filtered = _filter_shipments(
        SHIPMENTS,
        search=search,
        mode=mode,
        status=status,
        exception_type=exception_type,
        exceptions_only=exceptions_only,
    )

    return jsonify({
        "count": len(filtered),
        "shipments": [s.as_dict() for s in filtered],
    })


@app.route("/api/shipments/<shipment_id>")
def api_shipment_detail(shipment_id: str):
    """Return a single shipment as JSON."""
    shipment = SHIPMENT_MAP.get(shipment_id)
    if shipment is None:
        return jsonify({"error": f"Shipment {shipment_id} not found"}), 404
    return jsonify(shipment.as_dict())


@app.route("/api/metrics")
def api_metrics():
    """Return pilot metrics as JSON."""
    return jsonify(compute_metrics(SHIPMENTS))


if __name__ == "__main__":
    print("\n  Inbound Logistics Visibility Platform")
    print("  ======================================")
    print(f"  Loaded {len(SHIPMENTS)} shipments")
    print(f"  {sum(1 for s in SHIPMENTS if s.has_exceptions)} with exceptions")
    print(f"  AI features: {'ENABLED' if AI_FEATURES_ENABLED else 'DISABLED'}")
    print(f"\n  Open http://127.0.0.1:5000 in your browser\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
