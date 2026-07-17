# Contributing to Cricbuzz LiveStats Platform

Thank you for your interest in contributing to the **Cricbuzz LiveStats** project! We welcome code improvements, bug fixes, features, and documentation updates.

Please review the following contribution guidelines before getting started:

---

## Development Environment Setup

1. **Clone the Repository:**
   ```bash
   git clone <repository_url>
   cd cricbuzz-livestats
   ```

2. **Virtual Environment:**
   Initialize a Python virtual environment and activate it:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install flake8 black isort pytest
   ```

4. **Environment Variables:**
   Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```
   Add a valid `RAPIDAPI_KEY` to `.env` to pull live data.

---

## Code Quality Standards

We enforce strict formatting and style rules in our CI pipeline:

### 1. Imports Sorting (`isort`)
All imports must be cleanly sorted. Check imports sorting using:
```bash
isort --check-only .
```
To automatically sort imports, run:
```bash
isort .
```

### 2. Code Formatting (`black`)
We use the PEP-8 standard code formatter `black` (127 line limit max). Check formatting using:
```bash
black --check .
```
To format files automatically, run:
```bash
black .
```

### 3. Syntax and Style Linting (`flake8`)
We use `flake8` to scan for style violations and logical errors. Run lint checks via:
```bash
flake8 . --count --statistics
```

---

## Writing and Running Tests

All logic changes (transformers, clients, database mappings) should have corresponding tests in the `tests/` folder.
Run the complete unit test suite using:
```bash
pytest
```

---

## Pull Request Guidelines

1. **Branching:** Create a descriptive branch for your work (e.g. `feature/normalized-batting-averages` or `fix/potm-award-nan`).
2. **Local Validation:** Verify that `flake8`, `black`, `isort`, and `pytest` all pass locally before pushing.
3. **Commit Messages:** Use clear, declarative commit messages (e.g. `feat: add rolling average batsman stats query`).
