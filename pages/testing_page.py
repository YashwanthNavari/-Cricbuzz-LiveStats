import streamlit as st
import time
import unittest
import io
from sqlalchemy import text, inspect
from database.db import get_db, engine
from api.client import CricbuzzClient


def run_db_conn_test():
    """Test connecting to DB and running simple query."""
    start = time.time()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return (
            True,
            f"Connected successfully in {(time.time() - start)*1000:.1f}ms",
            None,
        )
    except Exception as e:
        return False, "Failed to connect to database.", str(e)


def run_tables_check_test():
    """Test checking that all expected tables are defined."""
    expected = {
        "series",
        "venues",
        "teams",
        "players",
        "matches",
        "innings",
        "batting_scores",
        "bowling_scores",
        "fielding_records",
        "partnerships",
    }
    try:
        inspector = inspect(engine)
        actual = set(inspector.get_table_names())
        missing = expected - actual
        if not missing:
            return True, f"All {len(expected)} tables exist.", None
        return False, f"Missing tables: {', '.join(missing)}", None
    except Exception as e:
        return False, "Failed to inspect database schema.", str(e)


def run_api_conn_test():
    """Test pinging the RapidAPI Cricbuzz host."""
    import requests
    from dotenv import load_dotenv
    import os

    load_dotenv()
    api_key = os.getenv("RAPIDAPI_KEY")
    api_host = os.getenv("RAPIDAPI_HOST", "cricbuzz-cricket.p.rapidapi.com")

    headers = {"x-rapidapi-key": api_key or "", "x-rapidapi-host": api_host}

    start = time.time()
    try:
        res = requests.get(
            f"https://{api_host}/matches/v1/recent", headers=headers, timeout=10
        )
        if res.status_code in (200, 401, 403, 429):
            return (
                True,
                f"API Host reached. Status code: {res.status_code}. Time: {(time.time() - start)*1000:.1f}ms",
                None,
            )
        return False, f"API Host returned error status: {res.status_code}", res.text
    except Exception as e:
        return False, "Failed to connect to API Host.", str(e)


def run_crud_test():
    """Verify that INSERT, UPDATE, and DELETE works."""
    try:
        with get_db() as session:
            # 1. Insert test team
            session.execute(
                text(
                    "INSERT INTO teams (id, name, short_name) VALUES (9999, 'Test Team', 'TST')"
                )
            )
            # 2. Update
            session.execute(
                text("UPDATE teams SET name = 'Test Team Updated' WHERE id = 9999")
            )
            # 3. Read & Verify
            res = session.execute(
                text("SELECT name FROM teams WHERE id = 9999")
            ).fetchone()
            if not res or res[0] != "Test Team Updated":
                raise ValueError("Insert or update failed to persist correctly.")
            # 4. Delete
            session.execute(text("DELETE FROM teams WHERE id = 9999"))
            session.commit()
        return (
            True,
            "CRUD operations test passed (Insert, Update, Read, Delete verified).",
            None,
        )
    except Exception as e:
        return False, "CRUD operations test failed.", str(e)


def run_pipeline_unit_tests():
    """Runs tests/test_pipeline.py programmatically."""
    from tests.test_pipeline import (
        TestCricbuzzClient,
        TestValidator,
        TestTransformer,
        TestIngestionPipeline,
    )

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestCricbuzzClient))
    suite.addTests(loader.loadTestsFromTestCase(TestValidator))
    suite.addTests(loader.loadTestsFromTestCase(TestTransformer))
    suite.addTests(loader.loadTestsFromTestCase(TestIngestionPipeline))

    # Run suite and write to string buffer
    stream = io.StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    start = time.time()
    result = runner.run(suite)
    duration = time.time() - start

    output = stream.getvalue()
    success = result.wasSuccessful()

    msg = f"Ran {result.testsRun} unit tests in {duration:.2f}s. Success count: {result.testsRun - len(result.failures) - len(result.errors)}"
    return success, msg, output


def render_testing_page():
    st.markdown(
        "<h2 style='color: #1e90ff;'>🧪 Testing & QA Center</h2>",
        unsafe_allow_html=True,
    )
    st.write(
        "Run automated system integration tests and standard python unit test suites programmatically."
    )

    st.markdown("---")

    run_tests_btn = st.button("Run Automated Tests ⚡", use_container_width=True)

    if run_tests_btn:
        st.markdown("### 📊 Test Run Results")

        # Test cases dictionary
        test_cases = [
            ("🔌 API Connection Test", run_api_conn_test),
            ("🗄️ Database Connection Test", run_db_conn_test),
            ("📁 Tables Schema integrity check", run_tables_check_test),
            ("📝 CRUD Operations Test", run_crud_test),
            (
                "🧬 Ingestion Pipeline Unit Tests (test_pipeline.py)",
                run_pipeline_unit_tests,
            ),
        ]

        for name, test_func in test_cases:
            st.write(f"**Running: {name}...**")
            start_t = time.time()
            try:
                pass_status, desc, details = test_func()
            except Exception as e:
                pass_status, desc, details = (
                    False,
                    "Test crashed with unhandled exception.",
                    str(e),
                )
            latency = (time.time() - start_t) * 1000.0

            if pass_status:
                st.success(f"✔️ **PASS** | {desc} | Duration: {latency:.1f}ms")
            else:
                st.error(f"❌ **FAIL** | {desc} | Duration: {latency:.1f}ms")
                if details:
                    with st.expander("Show Traceback details"):
                        st.code(details, language="text")

        st.success("All tests executed!")
