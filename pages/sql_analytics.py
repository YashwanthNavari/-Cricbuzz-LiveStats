import streamlit as st
import pandas as pd
import time
import io
import plotly.express as px
from sqlalchemy import text
from database.db import get_db
from database.queries import ANALYTICAL_QUERIES


def get_filter_options():
    """Fetches series, teams, and players lists from DB for parameter drop-downs."""
    series_list = [(-1, "All Series")]
    teams_list = []
    players_list = []

    try:
        with get_db() as session:
            # Series
            res_series = session.execute(
                text("SELECT id, name FROM series ORDER BY name")
            ).fetchall()
            for r in res_series:
                series_list.append((r[0], f"{r[1]} (ID: {r[0]})"))

            # Teams
            res_teams = session.execute(
                text("SELECT id, name FROM teams ORDER BY name")
            ).fetchall()
            for r in res_teams:
                teams_list.append((r[0], f"{r[1]} (ID: {r[0]})"))

            # Players
            res_players = session.execute(
                text("SELECT id, name FROM players ORDER BY name")
            ).fetchall()
            for r in res_players:
                players_list.append((r[0], f"{r[1]} (ID: {r[0]})"))
    except Exception as e:
        pass

    return series_list, teams_list, players_list


def render_sql_analytics():
    st.markdown(
        "<h2 style='color: #1e90ff;'>📊 SQL Analytics Engine</h2>",
        unsafe_allow_html=True,
    )
    st.write(
        "Execute and visualize the 25 pre-defined SQL queries using parameters selected directly from your database."
    )

    st.markdown("---")

    # Onboarding description
    st.markdown(
        """
    <div style='background-color: #1a202c; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 5px solid #00bfff;'>
        <h4 style='color: #00bfff; margin-top: 0; margin-bottom: 5px;'>📌 How to Run Analytics</h4>
        <p style='color: #a0aec0; font-size: 0.95rem; margin-bottom: 0;'>
            1. Select a category below to filter the 25 questions.<br>
            2. Expand any question card, adjust its input filters (such as target player or team), and click <b>Execute Query</b>.<br>
            3. The UI will show the exact SQL triggered, execution latency, results table, interactive charts, and CSV/Excel exports.
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Categorization of queries
    query_categories = {
        "🏆 All 25 Queries": list(ANALYTICAL_QUERIES.keys()),
        "📈 League Standings & Venues": ["Q1", "Q6", "Q10", "Q11", "Q12", "Q24", "Q25"],
        "🏏 Batting Analytics": ["Q2", "Q4", "Q7", "Q15", "Q17", "Q18", "Q19", "Q22"],
        "🥎 Bowling, Fielding & Extras": [
            "Q3",
            "Q5",
            "Q8",
            "Q9",
            "Q13",
            "Q14",
            "Q16",
            "Q20",
            "Q21",
            "Q23",
        ],
    }

    selected_cat = st.selectbox(
        "Filter Questions by Category", list(query_categories.keys())
    )
    allowed_keys = query_categories[selected_cat]

    # Load dynamic parameters mapping
    series_opts, team_opts, player_opts = get_filter_options()

    # Series options dict/lookup
    series_map = {label: val for val, label in series_opts}
    team_map = {label: val for val, label in team_opts}
    player_map = {label: val for val, label in player_opts}

    # Iterate through filtered queries
    for key in sorted(ANALYTICAL_QUERIES.keys(), key=lambda x: int(x[1:])):
        if key not in allowed_keys:
            continue

        q_info = ANALYTICAL_QUERIES[key]

        with st.expander(f"🔍 {key}: {q_info['title']}"):
            st.markdown(f"**Interpretation/Goal:** {q_info['description']}")

            # Render input selectors if parameters are needed
            bind_params = {}
            if q_info["params"]:
                st.markdown("**Query Input Controls:**")
                cols = st.columns(len(q_info["params"]))
                for idx, (p_name, p_type) in enumerate(q_info["params"].items()):
                    with cols[idx]:
                        if p_type == "series":
                            selected_label = st.selectbox(
                                f"Filter by Series ({p_name})",
                                list(series_map.keys()),
                                key=f"{key}_{p_name}",
                            )
                            bind_params[p_name] = series_map[selected_label]
                        elif p_type == "team":
                            selected_label = st.selectbox(
                                f"Filter by Team ({p_name})",
                                list(team_map.keys()),
                                key=f"{key}_{p_name}",
                                index=min(idx, len(team_map) - 1),
                            )
                            bind_params[p_name] = team_map[selected_label]
                        elif p_type == "player":
                            selected_label = st.selectbox(
                                f"Filter by Player ({p_name})",
                                list(player_map.keys()),
                                key=f"{key}_{p_name}",
                            )
                            bind_params[p_name] = player_map[selected_label]

            st.markdown("**SQL Executed:**")
            st.code(q_info["sql"], language="sql")

            # Run query button
            run_btn = st.button(f"Execute Query {key} ⚡", key=f"run_{key}")

            if run_btn:
                try:
                    start_time = time.time()
                    with get_db() as session:
                        sql_stmt = text(q_info["sql"])
                        # Read SQL query using pandas to display in dataframe
                        df_res = pd.read_sql_query(
                            sql_stmt, session.bind, params=bind_params
                        )

                    duration_ms = (time.time() - start_time) * 1000.0

                    st.success(f"Query completed in **{duration_ms:.2f} ms**")

                    if df_res.empty:
                        st.info("No matching records found for the chosen parameters.")
                    else:
                        st.subheader("Result Dataframe")
                        st.dataframe(df_res, use_container_width=True)

                        # Plotly visualisations
                        if q_info.get("chart_type") and q_info["chart_type"] != "table":
                            st.subheader("📊 Visualization")
                            c_type = q_info["chart_type"]
                            kw = q_info["chart_kwargs"]

                            # Clean chart arguments for plotting
                            if isinstance(kw, dict):
                                try:
                                    if c_type == "bar":
                                        fig = px.bar(
                                            df_res, **kw, template="plotly_dark"
                                        )
                                        st.plotly_chart(fig, use_container_width=True)
                                    elif c_type == "pie":
                                        fig = px.pie(
                                            df_res, **kw, template="plotly_dark"
                                        )
                                        st.plotly_chart(fig, use_container_width=True)
                                    elif c_type == "scatter":
                                        fig = px.scatter(
                                            df_res, **kw, template="plotly_dark"
                                        )
                                        st.plotly_chart(fig, use_container_width=True)
                                    elif c_type == "line":
                                        fig = px.line(
                                            df_res, **kw, template="plotly_dark"
                                        )
                                        st.plotly_chart(fig, use_container_width=True)
                                except Exception as chart_err:
                                    st.warning(
                                        f"Could not render Plotly chart: {chart_err}"
                                    )

                        # Export buttons
                        st.markdown("### Export Results")
                        exp_col1, exp_col2 = st.columns(2)

                        # CSV Export
                        csv_exp = df_res.to_csv(index=False)
                        exp_col1.download_button(
                            label="Export as CSV 📄",
                            data=csv_exp,
                            file_name=f"result_{key}.csv",
                            mime="text/csv",
                            key=f"csv_{key}",
                        )

                        # Excel Export
                        try:
                            buffer = io.BytesIO()
                            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                                df_res.to_excel(
                                    writer, index=False, sheet_name="Results"
                                )
                            excel_data = buffer.getvalue()
                            exp_col2.download_button(
                                label="Export as Excel 📈",
                                data=excel_data,
                                file_name=f"result_{key}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key=f"xlsx_{key}",
                            )
                        except Exception as excel_err:
                            exp_col2.error(f"Excel export unavailable: {excel_err}")

                except Exception as query_err:
                    st.error(f"SQL execution error: {query_err}")
