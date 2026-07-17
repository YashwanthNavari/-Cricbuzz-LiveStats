# System Architecture & Aesthetics

This document describes the package design, flat layout routing, and user interface aesthetic choices of the **Cricbuzz LiveStats** platform.

---

## 1. Project Directory Structure

The repository is structured as a flat Python project prepared for standard Git distribution:

```text
cricbuzz-livestats/
│
├── .github/
│   └── workflows/
│       └── python.yml          # GitHub Actions CI lint/test pipeline
│
├── api/                        # Cricbuzz API Integration Package
│   ├── __init__.py
│   ├── client.py               # Session manager, rate limiter, cache writer
│   ├── matches.py              # Matches list endpoints
│   ├── players.py              # Player profile endpoints
│   └── scorecard.py            # Detailed scorecard endpoints
│
├── assets/                     # Screenshots, diagrams, and media icons
│   ├── architecture/
│   ├── icons/
│   └── screenshots/
│
├── database/                   # Schema Models & Configurations
│   ├── __init__.py
│   ├── db.py                   # SQLAlchemy engine sessions & auto-migrations
│   ├── models.py               # 10 SQLAlchemy ORM models
│   ├── queries.py              # 25 pre-defined SQL queries
│   └── schema.sql              # Raw PostgreSQL schema DDL
│
├── docs/                       # Comprehensive System Documentation
│   ├── ARCHITECTURE.md
│   ├── API_MAPPING.md
│   ├── DATABASE_DESIGN.md
│   ├── DATASET_PIPELINE.md
│   └── SQL_ANALYTICS.md
│
├── logs/                       # Rotating runtime diagnostic file outputs
│   └── pipeline.log
│
├── pages/                      # Multipage Streamlit Dashboards
│   ├── __init__.py
│   ├── analytics_dashboard.py
│   ├── api_explorer.py
│   ├── crud_operations.py
│   ├── data_validation.py
│   ├── database_viewer.py
│   ├── dataset_builder.py
│   ├── home.py
│   ├── json_explorer.py
│   ├── logs_page.py
│   ├── performance_page.py
│   ├── sql_analytics.py
│   └── testing_page.py
│
├── processed_data/             # Ingestion run reports and exports
│   └── reports/
│
├── raw_data/                   # Local raw JSON file cache
│   ├── matches/
│   └── scorecards/
│
├── services/                   # Business Logic & Normalization Services
│   ├── __init__.py
│   ├── ingestion.py            # Ingestion pipeline orchestrator
│   ├── transformer.py          # Normalization transformers
│   └── validator.py            # Pydantic schema validation
│
├── tests/                      # Testing & QA Center
│   ├── __init__.py
│   └── test_pipeline.py        # Automated python unit tests
│
├── .env.example                # Template configuration settings
├── .gitignore                  # Git excluded directories
├── app.py                      # Streamlit entry point
├── CHANGELOG.md                # Release version summaries
├── CONTRIBUTING.md             # Quality standards & guidelines
├── LICENSE                     # License terms (MIT)
├── README.md                   # Onboarding setup instructions
├── run_pipeline.py             # CLI pipeline entry point
├── requirements.txt            # Package dependencies list
└── validate_dataset.py         # CLI dataset validation entry point
```

---

## 2. Platform Design & Styling Systems

The application interface is built to deliver a premium user experience via:
- **Consistent Dark Palette:** Custom CSS injections style layouts with custom color styling overrides (`#0e1117` backdrop, `#1f2937` side panels).
- **Clear Information Visual Hierarchy:** Important processes are grouped in cards using custom borders (e.g. blue borders for API indicators, green borders for validation results).
- **Interactive UI Micro-Animations:** Buttons have smooth transitions when hovered:
  ```css
  div.stButton > button:first-child {
      background-color: #1e90ff;
      transition: background 0.3s ease;
  }
  div.stButton > button:first-child:hover {
      background-color: #0073e6;
  }
  ```
- **Real-Time Data Visualization:** Uses Plotly's high-fidelity dark template charts to show points tables, leaderboard distributions, and database volumes.
