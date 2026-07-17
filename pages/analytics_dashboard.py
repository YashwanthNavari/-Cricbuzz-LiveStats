import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import text
from database.db import get_db


def render_analytics_dashboard():
    st.markdown(
        "<h2 style='color: #1e90ff;'>📈 Analytics Dashboard</h2>",
        unsafe_allow_html=True,
    )
    st.write(
        "Visually compare team head-to-head records, batsman strike rates, bowler economies, and venue performance statistics."
    )

    st.markdown("---")

    # Fetch lists of items for filters
    series_opts = [(-1, "All Series")]
    teams_opts = []
    players_opts = []

    try:
        with get_db() as session:
            # Series list
            res_series = session.execute(text("SELECT id, name FROM series")).fetchall()
            for r in res_series:
                series_opts.append((r[0], r[1]))

            # Teams list
            res_teams = session.execute(text("SELECT id, name FROM teams")).fetchall()
            teams_opts = [(r[0], r[1]) for r in res_teams]

            # Players list
            res_players = session.execute(
                text("SELECT id, name FROM players")
            ).fetchall()
            players_opts = [(r[0], r[1]) for r in res_players]
    except Exception:
        pass

    # Filters
    st.sidebar.subheader("Dashboard Filters")
    s_map = {name: s_id for s_id, name in series_opts}
    sel_series_name = st.sidebar.selectbox("Filter by Series", list(s_map.keys()))
    sel_series_id = s_map[sel_series_name]

    # ------------------ PANEL 1: LEADERBOARD OVERVIEW ------------------
    st.subheader("🏆 Tournament Leaders")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Top 5 Run Scorers**")
        sql_runs = """
        SELECT p.name AS "Player", SUM(bs.runs) AS "Runs", t.name AS "Team"
        FROM batting_scores bs
        JOIN players p ON bs.player_id = p.id
        JOIN innings i ON bs.innings_id = i.id
        JOIN matches m ON i.match_id = m.id
        JOIN teams t ON i.batting_team_id = t.id
        WHERE m.series_id = :series_id OR :series_id = -1
        GROUP BY p.id, p.name, t.name
        ORDER BY "Runs" DESC
        LIMIT 5;
        """
        try:
            with get_db() as session:
                df_runs = pd.read_sql_query(
                    text(sql_runs), session.bind, params={"series_id": sel_series_id}
                )
            if not df_runs.empty:
                fig = px.bar(
                    df_runs,
                    x="Runs",
                    y="Player",
                    color="Team",
                    orientation="h",
                    template="plotly_dark",
                    height=300,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No batting records found.")
        except Exception as e:
            st.error(f"Runs leaderboard failed: {e}")

    with col2:
        st.markdown("**Top 5 Wicket Takers**")
        sql_wickets = """
        SELECT p.name AS "Player", SUM(bowl.wickets) AS "Wickets", t.name AS "Team"
        FROM bowling_scores bowl
        JOIN players p ON bowl.player_id = p.id
        JOIN innings i ON bowl.innings_id = i.id
        JOIN matches m ON i.match_id = m.id
        JOIN teams t ON i.bowling_team_id = t.id
        WHERE m.series_id = :series_id OR :series_id = -1
        GROUP BY p.id, p.name, t.name
        ORDER BY "Wickets" DESC
        LIMIT 5;
        """
        try:
            with get_db() as session:
                df_wickets = pd.read_sql_query(
                    text(sql_wickets), session.bind, params={"series_id": sel_series_id}
                )
            if not df_wickets.empty:
                fig = px.bar(
                    df_wickets,
                    x="Wickets",
                    y="Player",
                    color="Team",
                    orientation="h",
                    template="plotly_dark",
                    height=300,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No bowling records found.")
        except Exception as e:
            st.error(f"Wickets leaderboard failed: {e}")

    # ------------------ PANEL 2: MATCH STATUSES ------------------
    st.markdown("---")
    st.subheader("🏟️ Match Summaries")

    col_live, col_rec = st.columns(2)
    with col_live:
        st.markdown("**🔴 Live Matches**")
        sql_live = """
        SELECT m.match_desc AS "Match", m.status AS "Status", t1.name || ' vs ' || t2.name AS "Teams"
        FROM matches m
        JOIN teams t1 ON m.team1_id = t1.id
        JOIN teams t2 ON m.team2_id = t2.id
        WHERE m.is_live = 1 OR m.is_live = 'true'
        """
        try:
            with get_db() as session:
                df_live = pd.read_sql_query(text(sql_live), session.bind)
            if not df_live.empty:
                st.dataframe(df_live, use_container_width=True)
            else:
                st.info("No live matches running currently.")
        except Exception as e:
            st.write(f"Live fetch error: {e}")

    with col_rec:
        st.markdown("**✅ Recent Matches**")
        sql_recent = """
        SELECT m.match_desc AS "Match", m.status AS "Result", s.name AS "Series"
        FROM matches m
        JOIN series s ON m.series_id = s.id
        WHERE m.is_completed = 1 OR m.is_completed = 'true'
        ORDER BY m.match_start_time DESC
        LIMIT 5
        """
        try:
            with get_db() as session:
                df_recent = pd.read_sql_query(text(sql_recent), session.bind)
            if not df_recent.empty:
                st.dataframe(df_recent, use_container_width=True)
            else:
                st.info("No completed matches found.")
        except Exception as e:
            st.write(f"Recent fetch error: {e}")

    # ------------------ PANEL 3: TEAM COMPARISONS ------------------
    st.markdown("---")
    st.subheader("⚔️ Team Comparison")

    if len(teams_opts) >= 2:
        t_map = {name: t_id for t_id, name in teams_opts}
        team_names = list(t_map.keys())

        tc_col1, tc_col2 = st.columns(2)
        with tc_col1:
            t1_sel = st.selectbox("Select Team A", team_names, index=0)
            t1_id = t_map[t1_sel]
        with tc_col2:
            t2_sel = st.selectbox(
                "Select Team B", team_names, index=min(1, len(team_names) - 1)
            )
            t2_id = t_map[t2_sel]

        sql_h2h = """
        SELECT 
            t.name AS "Team Name",
            COUNT(*) AS "Played",
            SUM(CASE WHEN m.winner_id = t.id THEN 1 ELSE 0 END) AS "Wins",
            SUM(CASE WHEN m.winner_id IS NOT NULL AND m.winner_id != t.id THEN 1 ELSE 0 END) AS "Losses"
        FROM matches m
        JOIN teams t ON t.id IN (m.team1_id, m.team2_id)
        WHERE (m.team1_id = :t1 AND m.team2_id = :t2)
           OR (m.team1_id = :t2 AND m.team2_id = :t1)
        GROUP BY t.id, t.name;
        """
        try:
            with get_db() as session:
                df_h2h = pd.read_sql_query(
                    text(sql_h2h), session.bind, params={"t1": t1_id, "t2": t2_id}
                )
            if not df_h2h.empty:
                fig = px.bar(
                    df_h2h,
                    x="Team Name",
                    y=["Wins", "Losses"],
                    barmode="group",
                    template="plotly_dark",
                    title=f"Head to Head: {t1_sel} vs {t2_sel}",
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(
                    "No head-to-head records found between these two teams in the database."
                )
        except Exception as e:
            st.error(f"H2H comparison failed: {e}")

    # ------------------ PANEL 4: PLAYER COMPARISONS ------------------
    st.markdown("---")
    st.subheader("🏃 Player Comparison")

    if len(players_opts) >= 2:
        p_map = {name: p_id for p_id, name in players_opts}
        player_names = list(p_map.keys())

        pc_col1, pc_col2 = st.columns(2)
        with pc_col1:
            p1_sel = st.selectbox("Select Player A", player_names, index=0)
            p1_id = p_map[p1_sel]
        with pc_col2:
            p2_sel = st.selectbox(
                "Select Player B", player_names, index=min(1, len(player_names) - 1)
            )
            p2_id = p_map[p2_sel]

        sql_p_comp = """
        SELECT 
            p.name AS "Player",
            COALESCE(SUM(bs.runs), 0) AS "Runs",
            COALESCE(SUM(bs.balls), 0) AS "Balls Faced",
            COALESCE(MAX(bs.runs), 0) AS "Highest Score"
        FROM players p
        LEFT JOIN batting_scores bs ON p.id = bs.player_id
        WHERE p.id IN (:p1, :p2)
        GROUP BY p.id, p.name;
        """
        try:
            with get_db() as session:
                df_p_comp = pd.read_sql_query(
                    text(sql_p_comp), session.bind, params={"p1": p1_id, "p2": p2_id}
                )
            if not df_p_comp.empty:
                fig = px.bar(
                    df_p_comp,
                    x="Player",
                    y="Runs",
                    color="Player",
                    text="Runs",
                    template="plotly_dark",
                    title="Runs Comparison",
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No comparative player records found.")
        except Exception as e:
            st.error(f"Player comparison failed: {e}")

    # ------------------ PANEL 5: VENUES & EXTRA HEATMAPS ------------------
    st.markdown("---")
    st.subheader("🏟️ Venues & Extra Heatmaps")

    sql_heatmap = """
    SELECT 
        v.name AS "Venue",
        i.innings_num AS "Innings Num",
        AVG(i.runs) AS "Avg Runs"
    FROM innings i
    JOIN matches m ON i.match_id = m.id
    JOIN venues v ON m.venue_id = v.id
    GROUP BY v.id, v.name, i.innings_num;
    """
    try:
        with get_db() as session:
            df_heat = pd.read_sql_query(text(sql_heatmap), session.bind)
        if not df_heat.empty:
            # Heatmap of Avg Runs across Venues and Innings
            fig = px.density_heatmap(
                df_heat,
                x="Innings Num",
                y="Venue",
                z="Avg Runs",
                text_auto=True,
                color_continuous_scale="Viridis",
                template="plotly_dark",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No venue stats available.")
    except Exception as e:
        st.write(f"Heatmap rendering error: {e}")
