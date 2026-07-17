import streamlit as st
from pathlib import Path


def render_logs_page():
    st.markdown(
        "<h2 style='color: #1e90ff;'>📜 Log Viewer</h2>", unsafe_allow_html=True
    )
    st.write(
        "Monitor system logs for API transactions, database transactions, parsing operations, and validation runs."
    )

    st.markdown("---")

    workspace_root = Path(__file__).resolve().parents[1]
    log_file_path = workspace_root / "logs" / "pipeline.log"

    if not log_file_path.exists():
        st.info(
            "No log file found. Once you run the API explorer or dataset builder, pipeline log streams will be written here."
        )
        return

    try:
        with open(log_file_path, "r", encoding="utf-8") as f:
            log_lines = f.readlines()
    except Exception as e:
        st.error(f"Failed to read log file: {e}")
        return

    st.write(f"Total Log Records: **{len(log_lines)}**")

    # Filtering interface
    col_level, col_search = st.columns([1, 2])

    with col_level:
        level_filter = st.selectbox(
            "Log Level Filter", ["ALL", "INFO", "WARNING", "ERROR", "CRITICAL"]
        )

    with col_search:
        search_filter = st.text_input("Filter by Keyword (e.g. CricbuzzClient)", "")

    # Apply filters
    filtered_lines = []
    for line in log_lines:
        # Check level
        if level_filter != "ALL":
            if f"[{level_filter}]" not in line:
                continue
        # Check search keyword
        if search_filter:
            if search_filter.lower() not in line.lower():
                continue
        filtered_lines.append(line)

    st.write(f"Filtered Log Records: **{len(filtered_lines)}**")

    # Display lines
    if filtered_lines:
        log_text = "".join(filtered_lines)
        st.text_area("Log Output Streams", value=log_text, height=450)

        # Download button
        st.download_button(
            label="Download Log File 📥",
            data=log_text,
            file_name="pipeline_filtered.log",
            mime="text/plain",
        )
    else:
        st.info("No logs match the chosen filter configuration.")
