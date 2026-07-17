import streamlit as st
import json
import os
import datetime
from pathlib import Path
from services.validator import validate_matches_json, validate_scorecard_json, validate_player_json

def get_all_raw_jsons(directory: Path):
    """Walks directory and returns list of relative paths for all json files."""
    json_files = []
    if not directory.exists():
        return json_files
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".json"):
                full_path = Path(root) / file
                json_files.append(full_path)
    return json_files

def render_json_explorer():
    st.markdown("<h2 style='color: #1e90ff;'>📂 JSON Explorer</h2>", unsafe_allow_html=True)
    st.write("Browse and analyze raw JSON responses saved inside the local `raw_data` cache folder.")
    
    st.markdown("---")
    
    workspace_root = Path(__file__).resolve().parents[1]
    raw_data_dir = workspace_root / "raw_data"
    
    json_files = get_all_raw_jsons(raw_data_dir)
    
    if not json_files:
        st.info("No raw JSON files found in `raw_data/` directory. Fetch some data first via API Explorer or Dataset Builder!")
        return
        
    # File selection dropdown
    file_options = {str(f.relative_to(raw_data_dir)): f for f in json_files}
    selected_rel_path = st.selectbox("Select JSON Cache File", list(file_options.keys()))
    selected_file_path = file_options[selected_rel_path]
    
    # Load JSON content
    try:
        with open(selected_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        st.error(f"Failed to read file: {e}")
        return
        
    # File details
    stat = selected_file_path.stat()
    file_size_kb = stat.st_size / 1024.0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("File Size", f"{file_size_kb:.2f} KB")
    time_str = os.path.getmtime(selected_file_path)
    time_formatted = datetime.datetime.fromtimestamp(time_str).strftime('%Y-%m-%d %H:%M:%S')
    col2.metric("Modified Date", time_formatted)
    
    # Check schema validator
    is_valid = False
    schema_type = "Unknown"
    if "matches" in selected_rel_path:
        is_valid = validate_matches_json(data)
        schema_type = "Matches List Schema"
    elif "hscard" in selected_rel_path:
        is_valid = validate_scorecard_json(data)
        schema_type = "Match Scorecard Schema"
    elif "player" in selected_rel_path:
        is_valid = validate_player_json(data)
        schema_type = "Player Details Schema"
        
    col3.metric("Validation Check", "PASS" if is_valid else "FAIL")
    st.info(f"Target Schema Class: **{schema_type}**")
    
    # Missing / Duplicate keys analysis
    st.subheader("📊 Structural Key Statistics")
    
    # Run a simple diagnostic to find null/empty values or nested lists size
    null_keys = []
    def check_nulls(d, path=""):
        if isinstance(d, dict):
            for k, v in d.items():
                curr_path = f"{path}.{k}" if path else k
                if v is None:
                    null_keys.append(curr_path)
                else:
                    check_nulls(v, curr_path)
        elif isinstance(d, list):
            for idx, item in enumerate(d):
                check_nulls(item, f"{path}[{idx}]")
                
    check_nulls(data)
    
    col_metric1, col_metric2 = st.columns(2)
    col_metric1.metric("Total Missing/NULL Fields", len(null_keys))
    
    # Calculate depth
    def get_max_depth(d):
        if isinstance(d, dict) and d:
            return 1 + max(get_max_depth(v) for v in d.values())
        elif isinstance(d, list) and d:
            return 1 + max(get_max_depth(item) for item in d)
        return 0
        
    col_metric2.metric("Max Nested JSON Depth", get_max_depth(data))
    
    if null_keys:
        with st.expander("Show NULL fields path"):
            st.write(null_keys)
            
    st.markdown("---")
    
    # JSON Content and search
    st.subheader("🔍 JSON Contents Viewer")
    
    search_query = st.text_input("Search term in JSON")
    
    # Search functionality
    if search_query:
        found_matches = []
        def search_json(d, path=""):
            if isinstance(d, dict):
                for k, v in d.items():
                    curr_path = f"{path}.{k}" if path else k
                    if search_query.lower() in str(k).lower() or search_query.lower() in str(v).lower():
                        found_matches.append((curr_path, str(v)))
                    search_json(v, curr_path)
            elif isinstance(d, list):
                for idx, item in enumerate(d):
                    search_json(item, f"{path}[{idx}]")
                    
        search_json(data)
        st.write(f"Found {len(found_matches)} matches:")
        for path, val in found_matches[:30]:
            st.markdown(f"- `{path}`: `{val}`")
            
    # Pretty JSON View
    st.json(data)
    
    # Download JSON button
    st.download_button(
        label="Download Raw JSON",
        data=json.dumps(data, indent=2),
        file_name=selected_file_path.name,
        mime="application/json"
    )
