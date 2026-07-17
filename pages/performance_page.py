import streamlit as st
import pandas as pd
import time
from sqlalchemy import text
from database.db import get_db


def run_performance_benchmarks():
    """Measures connection latency and runs performance queries."""
    benchmarks = []

    # 1. Simple Select
    start = time.time()
    try:
        with get_db() as session:
            session.execute(text("SELECT 1")).scalar()
        latency_ms = (time.time() - start) * 1000.0
        benchmarks.append(
            {
                "Task": "Simple Ping Connection (SELECT 1)",
                "Latency (ms)": round(latency_ms, 2),
                "Status": "PASS",
            }
        )
    except Exception as e:
        benchmarks.append(
            {
                "Task": "Simple Ping Connection (SELECT 1)",
                "Latency (ms)": 0.0,
                "Status": f"FAIL: {e}",
            }
        )

    # 2. Count matches
    start = time.time()
    try:
        with get_db() as session:
            session.execute(text("SELECT COUNT(*) FROM matches")).scalar()
        latency_ms = (time.time() - start) * 1000.0
        benchmarks.append(
            {
                "Task": "Fetch Matches Volume Count",
                "Latency (ms)": round(latency_ms, 2),
                "Status": "PASS",
            }
        )
    except Exception as e:
        benchmarks.append(
            {
                "Task": "Fetch Matches Volume Count",
                "Latency (ms)": 0.0,
                "Status": f"FAIL: {e}",
            }
        )

    # 3. Join matches and teams
    start = time.time()
    try:
        with get_db() as session:
            session.execute(text("""
                SELECT m.id, t1.name, t2.name 
                FROM matches m
                JOIN teams t1 ON m.team1_id = t1.id
                JOIN teams t2 ON m.team2_id = t2.id
                LIMIT 10
            """)).fetchall()
        latency_ms = (time.time() - start) * 1000.0
        benchmarks.append(
            {
                "Task": "Join Matches & Teams (10 Rows Limit)",
                "Latency (ms)": round(latency_ms, 2),
                "Status": "PASS",
            }
        )
    except Exception as e:
        benchmarks.append(
            {
                "Task": "Join Matches & Teams (10 Rows Limit)",
                "Latency (ms)": 0.0,
                "Status": f"FAIL: {e}",
            }
        )

    # 4. Complex aggregating query (Points Table Q1)
    start = time.time()
    try:
        with get_db() as session:
            session.execute(text("""
                SELECT batting_team_id, SUM(runs) AS total_runs
                FROM innings
                GROUP BY batting_team_id
            """)).fetchall()
        latency_ms = (time.time() - start) * 1000.0
        benchmarks.append(
            {
                "Task": "Aggregating Runs by Team (Innings Group By)",
                "Latency (ms)": round(latency_ms, 2),
                "Status": "PASS",
            }
        )
    except Exception as e:
        benchmarks.append(
            {
                "Task": "Aggregating Runs by Team (Innings Group By)",
                "Latency (ms)": 0.0,
                "Status": f"FAIL: {e}",
            }
        )

    return benchmarks


def render_performance_page():
    st.markdown(
        "<h2 style='color: #1e90ff;'>⚡ Performance & Latency Center</h2>",
        unsafe_allow_html=True,
    )
    st.write(
        "Measure connection latency, query times, index effectiveness, and database optimization statistics."
    )

    st.markdown("---")

    # Overview of performance stats
    st.subheader("📊 Relational Index Statistics")
    st.write(
        "The database implements indexes on foreign keys and commonly searched filters to ensure sub-millisecond querying latency:"
    )

    st.markdown("""
    - `idx_matches_series`: Speeds up points table calculation and tournament filters.
    - `idx_matches_live`: Used for active dashboard real-time scores rendering.
    - `idx_batting_player` & `idx_bowling_player`: Optimizes player card analytics.
    """)

    st.subheader("⚙️ Run Live Database Benchmarks")
    run_btn = st.button("Trigger Performance Diagnostics ⚡", use_container_width=True)

    if run_btn:
        with st.spinner("Executing query workloads..."):
            bench_results = run_performance_benchmarks()

        df_bench = pd.DataFrame(bench_results)
        st.dataframe(df_bench, use_container_width=True)

        # Plot visual metrics
        import plotly.express as px

        fig = px.bar(
            df_bench,
            x="Latency (ms)",
            y="Task",
            color="Status",
            orientation="h",
            template="plotly_dark",
            title="Query Latency Benchmarks (lower is better)",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.success("Database benchmarks completed successfully!")
