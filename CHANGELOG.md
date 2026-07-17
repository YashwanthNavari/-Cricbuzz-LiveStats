# Changelog

All notable changes to the **Cricbuzz LiveStats** platform will be documented in this file.

---

## [1.0.0] - 2026-07-17

### Added
- **Normalized Relational SQL Schema:** 10 core tables defined in 3NF (Third Normal Form) supporting SQLite and PostgreSQL databases.
- **Automated ETL Pipeline:** Robust parser mapping nested JSON payloads from Cricbuzz RapidAPI to database rows with error retries and resume checkpoints.
- **Multipage Streamlit Application:** Interactive views including:
  - `Home`: Dashboard volume charts and onboarding overview.
  - `API Explorer`: Interface to test endpoints and check request latencies.
  - `JSON Explorer`: File-cache browser with search filters.
  - `Dataset Builder`: Run and monitor the ETL ingestion process.
  - `Database Viewer`: Pagination explorer for SQL tables.
  - `Data Validation`: Diagnostics for duplicates, broken links, and overs format repairs.
  - `SQL Analytics`: Interactive runner for 25 pre-defined cricket questions.
  - `CRUD Operations`: Create, read, update, and delete screens.
  - `Analytics Dashboard`: Comparative team/player charts and heatmaps.
  - `Log Viewer`: Real-time application log stream analyzer.
  - `Testing & QA Center`: Automated database, API, and unit test suites execution.
  - `Performance Monitor`: Database benchmark graphs.
- **Robust Schema Migrations:** Auto-run `ALTER TABLE` operations on startup to upgrade schemas without losing local data.
- **GitHub Actions Workflows:** Python CI running black, isort, flake8, and pytest.
