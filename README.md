# Inbound Logistics Visibility Platform

Single source of truth for inbound shipments. Exception-first, operator-friendly, pilot-ready.

## What it does

Surfaces what is late, stale, or at risk — early enough to act. No ERP changes, no system replacements, no buzzwords.

**"I know what's late, why it's late, and what needs attention today."**

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 in your browser.

## Features

- **Exception-first dashboard** — shipments sorted by severity, not alphabetically
- **Filterable and searchable** — by vendor, mode, status, exception type, or any reference number
- **Drill-down detail view** — exception summary, ETA vs plan, milestone timeline, all reference numbers
- **Raw JSON access** — full transparency, no hidden logic
- **Pilot metrics** — operational metrics that track real value, not vanity numbers
- **AI features** (optional, off by default) — explain exceptions, summarize changes, draft vendor messages

## Exception Logic

| Exception | Trigger | Default Threshold |
|-----------|---------|-------------------|
| **Late** | Current ETA slipped beyond planned ETA | 24 hours |
| **Stale** | No tracking update received | 48 hours |
| **At Risk** | ETA within watch window, not delivered | 3 days |

All thresholds are configurable in `config.py`.

## Project Structure

```
app.py                  # Flask application
config.py               # Configurable thresholds and settings
models.py               # Data models (Shipment, Milestone, Exception)
exception_engine.py     # Exception detection logic
seed_data.py            # Pseudo data for MVP testing
ai_features.py          # Feature-flagged AI capabilities
metrics.py              # Pilot success metrics
templates/              # Jinja2 HTML templates
static/style.css        # Operator-friendly styling
```

## Configuration

Edit `config.py` to adjust:

- Exception thresholds (late hours, stale hours, at-risk days)
- Severity scoring weights
- AI feature toggle (`AI_FEATURES_ENABLED`)
- Pilot baseline values for metric comparison

## Data Philosophy

- Read-only ingestion — no writes to any upstream system
- Pseudo data for MVP — designed to later accept CSV, ERP exports, flat files, or APIs
- Transparency — raw JSON always available for every shipment

## API Endpoints

- `GET /api/shipments` — all shipments (supports same query params as dashboard)
- `GET /api/shipments/<id>` — single shipment detail
- `GET /api/metrics` — pilot metrics as JSON
