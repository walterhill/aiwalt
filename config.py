"""
Configuration for the inbound logistics visibility platform.

All thresholds are configurable. Adjust these for your operation's
tolerances before going live.
"""

from datetime import timedelta


# --- Exception Thresholds ---

# Late: current ETA has slipped beyond planned ETA by more than this many hours.
LATE_THRESHOLD_HOURS = 24

# Stale: no tracking update received within this many hours.
STALE_THRESHOLD_HOURS = 48

# At-risk: shipment ETA is within this many days and status is not "Delivered".
AT_RISK_DAYS = 3

# --- Severity Scoring ---
# Higher = more urgent. Used for default sort order on dashboard.
SEVERITY_WEIGHTS = {
    "late": 30,
    "stale": 20,
    "at_risk": 10,
}

# Bonus severity points per full day of ETA slip.
LATE_SEVERITY_PER_DAY = 5

# Bonus severity points per full day without an update beyond the stale window.
STALE_SEVERITY_PER_DAY = 3


# --- Display ---

# How many shipments to show per page on the dashboard.
PAGE_SIZE = 50

# Date/time display format across the UI.
DATETIME_FORMAT = "%Y-%m-%d %H:%M %Z"
DATE_FORMAT = "%Y-%m-%d"


# --- AI Features ---

# Master toggle. Set to True to enable AI-powered explanations,
# change summaries, and vendor message drafts.
AI_FEATURES_ENABLED = False


# --- Pilot Metrics ---

# Baseline values (pre-pilot) for comparison. Update these with
# your actual pre-pilot measurements before starting the pilot.
PILOT_BASELINE = {
    "avg_reporting_minutes_per_day": 90,
    "avg_delay_detection_hours": 48,
    "avg_status_questions_per_day": 25,
    "data_corrections_per_week": 12,
}


# --- Data Ingestion ---

# For MVP, data comes from seed_data.py. These placeholders document
# where real integrations would connect.
DATA_SOURCES = {
    "csv_upload": False,
    "erp_export": False,
    "flat_file": False,
    "api": False,
}
