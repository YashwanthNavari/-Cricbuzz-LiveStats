import streamlit as st
import logging
from pathlib import Path
from services.ingestion import IngestionPipeline
from database.db import get_db
from database.models import Match

# Global lists for capturing logs
st_log_messages = []


class StLogHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        st_log_messages.append(log_entry)


def render_dataset_builder():
    st.markdown(
        "<h2 style='color: #1e90ff;'>⚙️ Dataset Builder</h2>", unsafe_allow_html=True
    )
    st.write(
        "Populate your local SQL database by running the Cricbuzz RapidAPI ETL (Extract, Transform, Load) ingestion pipeline."
    )

    st.markdown("---")

    # Onboarding help card
    st.markdown(
        """
    <div style='background-color: #1a202c; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 5px solid #00bfff;'>
        <h4 style='color: #00bfff; margin-top: 0; margin-bottom: 8px;'>💡 Pipeline Operation Details</h4>
        <p style='color: #a0aec0; font-size: 0.95rem; margin-bottom: 0; line-height: 1.5;'>
            When you trigger the pipeline, the system performs a multi-stage ETL flow:<br>
            1. <b>Extract:</b> Hits the Cricbuzz API to find match listings of the selected type.<br>
            2. <b>Cache:</b> Writes the raw JSON files directly into <code>raw_data/matches/</code>.<br>
            3. <b>Fetch Scorecards:</b> Iterates over each match, fetching details only if the match does not already exist in the database (converts API quota).<br>
            4. <b>Normalize:</b> Normalizes series, venues, teams, players, wickets, batting, bowling, and partnerships into SQL.
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    col_ctrl, col_stats = st.columns([1, 1])

    with col_ctrl:
        st.subheader("🚀 Control Panel")
        match_type = st.radio(
            "Select Ingestion Target Category",
            ["recent", "live", "upcoming"],
            help="Recent fetches completed scorecards. Live targets active matches. Upcoming retrieves schedule slots.",
        )

        # Start button
        run_btn = st.button("Start Ingestion Pipeline ⚙️", use_container_width=True)

    with col_stats:
        st.subheader("📊 Ingestion Volume")
        # Check database current matches count
        try:
            with get_db() as session:
                match_count = session.query(Match).count()
        except Exception:
            match_count = 0

        st.metric("Total Matches in Database", match_count)
        st.info(
            "🔄 Resume capability: Active. Match details already residing in the database will be automatically skipped to conserve your RapidAPI quota."
        )

    if run_btn:
        st_log_messages.clear()

        # Add handler to root logger
        root_logger = logging.getLogger()
        handler = StLogHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        root_logger.addHandler(handler)

        st.markdown("### 🔄 Ingestion In Progress")
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            # Stage 1
            status_text.text(
                "Connecting to RapidAPI Host and pulling match listings..."
            )
            progress_bar.progress(20)

            pipeline = IngestionPipeline()

            # Stage 2
            status_text.text(
                "Downloading raw scorecard payloads and writing local cache..."
            )
            progress_bar.progress(50)

            # Stage 3
            status_text.text(
                "Parsing scorecards and writing normalized tables into SQL..."
            )
            progress_bar.progress(80)

            results = pipeline.ingest_matches_list(match_type=match_type)

            progress_bar.progress(100)
            status_text.text("Ingestion completed successfully!")

            # Displays counters
            st.success("🎉 Ingestion Pipeline finished running successfully!")

            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("Matches Discovered", results.get("matches_ingested", 0))
            sc2.metric(
                "New Scorecards normalise", results.get("scorecards_ingested", 0)
            )
            sc3.metric("Errors Logged", results.get("errors", 0))

            if results.get("error_details"):
                st.warning("Skipped matches or non-fatal warnings:")
                for error in results["error_details"]:
                    st.write(f"- {error}")

        except Exception as e:
            st.error(f"Pipeline Execution Failed: {e}")
            logging.error(f"Pipeline Execution Failed: {e}", exc_info=True)
            progress_bar.progress(100)
            status_text.text("Pipeline crashed.")

        finally:
            # Remove custom logging handler
            root_logger.removeHandler(handler)

        # Display logs
        if st_log_messages:
            st.subheader("📜 Real-Time Ingestion Logs")
            st.code("\n".join(st_log_messages), language="text")
