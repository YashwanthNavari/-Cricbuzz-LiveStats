import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from database.db import get_db
from database.models import Series, Venue, Team, Player, Match, Innings, BattingScore, BowlingScore

def render_home():
    st.markdown("<h1 style='text-align: center; color: #1e90ff;'>🏏 Cricbuzz LiveStats Platform</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #888;'>Real-Time Cricket Data Ingestion, Normalization, and Analytics Dashboard</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Onboarding quick start guide
    st.markdown("""
    <div style='background-color: #1a202c; padding: 18px; border-radius: 8px; border-left: 5px solid #1e90ff; margin-bottom: 25px;'>
        <h4 style='color: #1e90ff; margin-top: 0;'>🚀 Quick Start Guide - How to use this platform</h4>
        <ol style='color: #cbd5e0; margin-bottom: 0; line-height: 1.6;'>
            <li>Navigate to <b>🔌 API Explorer</b> in the sidebar to verify your Cricbuzz RapidAPI credentials and ping the endpoints.</li>
            <li>Go to <b>⚙️ Dataset Builder</b> to download and ingest match scorecards into the SQL database.</li>
            <li>Browse the raw normalized rows and schemas in the <b>🗄️ Database Viewer</b>.</li>
            <li>Run data quality audits and formatting checks in <b>🛡️ Data Validation</b>.</li>
            <li>Run and visualize the 25 complex pre-defined queries in <b>📊 SQL Analytics</b> or explore team comparisons in the <b>📈 Analytics Dashboard</b>.</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    
    # Live stats
    st.subheader("📊 Live Database Volume & Statistics")
    
    stats = {}
    try:
        with get_db() as session:
            stats["Series"] = session.query(Series).count()
            stats["Venues"] = session.query(Venue).count()
            stats["Teams"] = session.query(Team).count()
            stats["Players"] = session.query(Player).count()
            stats["Matches"] = session.query(Match).count()
            stats["Innings"] = session.query(Innings).count()
            stats["Batting"] = session.query(BattingScore).count()
            stats["Bowling"] = session.query(BowlingScore).count()
    except Exception as e:
        st.error(f"Failed to connect to database to fetch stats: {e}")
        stats = {k: 0 for k in ["Series", "Venues", "Teams", "Players", "Matches", "Innings", "Batting", "Bowling"]}
        
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("🏆 Series", stats["Series"])
    m_col1.metric("🏟️ Venues", stats["Venues"])
    
    m_col2.metric("👥 Teams", stats["Teams"])
    m_col2.metric("🏃 Players", stats["Players"])
    
    m_col3.metric("🏏 Matches", stats["Matches"])
    m_col3.metric("📊 Innings", stats["Innings"])
    
    m_col4.metric("🪵 Batting Records", stats["Batting"])
    m_col4.metric("🥎 Bowling Records", stats["Bowling"])
    
    # Render table size chart
    df_stats = pd.DataFrame([
        {"Entity": k, "Record Count": v} for k, v in stats.items()
    ])
    
    fig = px.bar(
        df_stats, 
        x="Record Count", 
        y="Entity", 
        color="Entity", 
        orientation="h",
        template="plotly_dark",
        height=280,
        title="Database Records Volume Breakdown"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Architecture & Schema Map
    col_left, col_right = st.columns([3, 2])
    
    with col_left:
        st.subheader("💡 System Architecture")
        st.markdown("""
        **Cricbuzz LiveStats** operates as a normalized 3NF relational data warehouse:
        - **Pipeline Ingestion:** Download endpoints run asynchronously with retries, mapping payload responses locally inside `raw_data/` before parsing.
        - **Schema Normalizer:** Transforms nested, raw API arrays into relational structures for Series, Teams, Players, Matches, and scorecard metrics.
        - **Quality Verification:** Standardizes decimals for cricket overs (e.g. converting `15.6` balls into clean integer targets), verifying foreign key integrity dynamically.
        """)
        
    with col_right:
        st.subheader("🔗 Relational Schema Map")
        st.markdown("""
        The database consists of **10 interconnected relational tables**:
        1. **`series`**: Match tournaments and leagues.
        2. **`venues`**: Stadium capacities and locations.
        3. **`teams`**: Country and franchise rosters.
        4. **`players`**: Athlete names, bowling/batting roles.
        5. **`matches`**: Game summaries, overs limit, and POTM awards.
        6. **`innings`**: Team scores, wickets, and extras.
        7. **`batting_scores`**: Individual runs, balls faced, and dismissal types.
        8. **`bowling_scores`**: Overs bowled, maidens, runs conceded, and wickets.
        9. **`fielding_records`**: Catches, stumpings, and run-outs per innings.
        10. **`partnerships`**: Pair pairing run records.
        """)
