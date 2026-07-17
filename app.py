import streamlit as st
import logging
from pathlib import Path
from dotenv import load_dotenv

# Import pages
from pages.home import render_home
from pages.api_explorer import render_api_explorer
from pages.json_explorer import render_json_explorer
from pages.dataset_builder import render_dataset_builder
from pages.database_viewer import render_database_viewer
from pages.data_validation import render_data_validation
from pages.sql_analytics import render_sql_analytics
from pages.crud_operations import render_crud_operations
from pages.analytics_dashboard import render_analytics_dashboard
from pages.logs_page import render_logs_page
from pages.testing_page import render_testing_page
from pages.performance_page import render_performance_page

# Load environment configs
load_dotenv()

# Setup root logging to file for logs_page capture
workspace_root = Path(__file__).resolve().parent
logs_dir = workspace_root / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)
log_file = logs_dir / "pipeline.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8")
    ]
)

# Page Setup
st.set_page_config(page_title="Cricbuzz LiveStats Dashboard", page_icon="🏏", layout="wide")

# Custom Dark Mode styling
st.markdown("""
<style>
    /* Dark theme wrapper overrides */
    .reportview-container {
        background: #0e1117;
        color: #fafafa;
    }
    /* Streamlit sidebar container */
    .sidebar .sidebar-content {
        background: #1f2937;
    }
    /* Buttons custom hover styling */
    div.stButton > button:first-child {
        background-color: #1e90ff;
        color: white;
        border-radius: 6px;
        border: none;
        transition: background 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #0073e6;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.sidebar.markdown("<h2 style='text-align: center; color: #1e90ff;'>🏏 LiveStats Navigation</h2>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
    pages = {
        "🏠 Home": render_home,
        "🔌 API Explorer": render_api_explorer,
        "📂 JSON Explorer": render_json_explorer,
        "⚙️ Dataset Builder": render_dataset_builder,
        "🗄️ Database Viewer": render_database_viewer,
        "🛡️ Data Validation": render_data_validation,
        "📊 SQL Analytics": render_sql_analytics,
        "🛠️ CRUD Operations": render_crud_operations,
        "📈 Analytics Dashboard": render_analytics_dashboard,
        "📜 Log Viewer": render_logs_page,
        "🧪 Testing Page": render_testing_page,
        "⚡ Performance Monitor": render_performance_page
    }
    
    selected_page_name = st.sidebar.radio("Select View", list(pages.keys()))
    
    st.sidebar.markdown("---")
    st.sidebar.info("Cricbuzz LiveStats Platform v1.0. Developed using ONLY real Cricbuzz RapidAPI data.")
    
    # Render selected view
    try:
        pages[selected_page_name]()
    except Exception as e:
        st.error("### ⚠️ Application Error")
        st.write("An unexpected error occurred during rendering this page. Check details below:")
        st.exception(e)

if __name__ == "__main__":
    main()
