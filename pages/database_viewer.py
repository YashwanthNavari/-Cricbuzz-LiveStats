import streamlit as st
import pandas as pd
from sqlalchemy import inspect, text
from database.db import get_db, engine

def render_database_viewer():
    st.markdown("<h2 style='color: #1e90ff;'>🗄️ Database Viewer</h2>", unsafe_allow_html=True)
    st.write("Browse table schemas, primary keys, foreign keys, indexes, and preview normalized data records with pagination.")
    
    st.markdown("---")
    
    # Inspect tables list
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if not tables:
        st.warning("No tables found in the database. Execute the pipeline or initialize the schema first.")
        return
        
    selected_table = st.selectbox("Select Database Table to Inspect", tables)
    
    # Schema metadata
    st.subheader(f"📋 Schema details for: `{selected_table}`")
    
    columns = inspector.get_columns(selected_table)
    col_df = pd.DataFrame([
        {
            "Column Name": c["name"],
            "Data Type": str(c["type"]),
            "Nullable": c["nullable"],
            "Default": str(c.get("default", "None"))
        } for c in columns
    ])
    
    # Keys / Constraints
    pk = inspector.get_pk_constraint(selected_table).get("constrained_columns", [])
    fks = inspector.get_foreign_keys(selected_table)
    indexes = inspector.get_indexes(selected_table)
    
    c_meta1, c_meta2, c_meta3 = st.columns(3)
    c_meta1.write("**🔑 Primary Key(s):**")
    c_meta1.code(", ".join(pk) if pk else "None")
    
    c_meta2.write("**🔗 Foreign Key Constraints:**")
    if fks:
        for fk in fks:
            constrained = ", ".join(fk["constrained_columns"])
            referred = f"{fk['referred_table']}({', '.join(fk['referred_columns'])})"
            c_meta2.code(f"{constrained} -> {referred}")
    else:
        c_meta2.code("None")
        
    c_meta3.write("**⚡ Indexes:**")
    if indexes:
        for idx in indexes:
            c_meta3.code(f"{idx['name']} ({', '.join(idx['column_names'])})")
    else:
        c_meta3.code("None")
        
    st.dataframe(col_df, use_container_width=True)
    
    # Preview and Search
    st.markdown("---")
    st.subheader(f"🔍 Paginated Data Preview ({selected_table})")
    
    # Search filter
    search_term = st.text_input("Filter records containing text", "")
    
    # Pagination configuration
    page_size = st.selectbox("Rows per page", [10, 25, 50, 100], index=0)
    
    # Fetch data
    try:
        query_sql = f"SELECT * FROM {selected_table}"
        with get_db() as session:
            # For large tables, fetch limited or run count
            count_sql = f"SELECT COUNT(*) FROM {selected_table}"
            total_records = session.execute(text(count_sql)).scalar()
            
            # Load into pandas to paginate/search easily
            df_preview = pd.read_sql_query(text(query_sql), session.bind)
            
        if df_preview.empty:
            st.info("Table is empty.")
            return
            
        # Perform text search in pandas
        if search_term:
            # Filter rows where any column contains search_term
            mask = df_preview.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)
            df_filtered = df_preview[mask]
        else:
            df_filtered = df_preview
            
        filtered_count = len(df_filtered)
        st.write(f"Showing {filtered_count} of {total_records} total records in table.")
        
        # Calculate pages
        import math
        total_pages = max(1, math.ceil(filtered_count / page_size))
        page_num = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
        
        start_idx = (page_num - 1) * page_size
        end_idx = start_idx + page_size
        
        st.dataframe(df_filtered.iloc[start_idx:end_idx], use_container_width=True)
        
        # Download data option
        csv_data = df_filtered.to_csv(index=False)
        st.download_button(
            label=f"Download {selected_table} Data as CSV",
            data=csv_data,
            file_name=f"{selected_table}_export.csv",
            mime="text/csv"
        )
        
    except Exception as e:
        st.error(f"Error loading preview for table `{selected_table}`: {e}")
