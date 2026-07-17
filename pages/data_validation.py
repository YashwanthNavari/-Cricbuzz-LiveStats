import streamlit as st
import pandas as pd
from validate_dataset import DatasetValidator

def render_data_validation():
    st.markdown("<h2 style='color: #1e90ff;'>🛡️ Data Validation & Quality</h2>", unsafe_allow_html=True)
    st.write("Ensure data consistency. Run diagnostics for duplicates, broken links, missing attributes, or bad formatting.")
    
    st.markdown("---")
    
    # Validation glossary card
    st.markdown("""
    <div style='background-color: #1a202c; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 5px solid #00ff7f;'>
        <h4 style='color: #00ff7f; margin-top: 0; margin-bottom: 8px;'>📋 Active Integrity Rules</h4>
        <ul style='color: #a0aec0; font-size: 0.95rem; margin-bottom: 0; line-height: 1.5; padding-left: 20px;'>
            <li><b>Duplicate Check:</b> Scans for duplicate player records (identical IDs/names), duplicate venues, or duplicate team registers.</li>
            <li><b>Missing Primary Keys:</b> Scans key tables for records missing mandatory IDs or unique values.</li>
            <li><b>Broken Foreign Keys:</b> Finds orphaned innings or scores (e.g. scores referencing a player or match that was deleted).</li>
            <li><b>Overs Format Violations:</b> Scans for incorrect over decimals. Since cricket overs consist of 6 balls, values like <code>14.6</code> or <code>14.7</code> are invalid. The system flags these.</li>
            <li><b>Auto-Fix Engine:</b> Automatically repairs invalid overs formats in the database by rounding them up to correct integer bounds (e.g. <code>14.6</code> $\rightarrow$ <code>15.0</code>).</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    validator = DatasetValidator()
    
    col_ctrl, col_act = st.columns([2, 1])
    
    with col_ctrl:
        st.write("Click below to run a validation check against all relational tables in the database:")
        check_clicked = st.button("Run Diagnostic Check 🔍", use_container_width=True)
        
    with col_act:
        st.write("Run the Auto-Fix engine to repair formatting anomalies (e.g. over counts):")
        fix_clicked = st.button("Run Auto-Fix Engine 🔧", use_container_width=True)
        
    # Auto fix execution
    if fix_clicked:
        st.markdown("### 🛠️ Auto-Fix Progress")
        try:
            repaired_count = validator.auto_fix_issues()
            if repaired_count > 0:
                st.success(f"Auto-fix completed successfully! Repaired {repaired_count} over format records in the database.")
            else:
                st.info("Validation run clean. No format repairs needed.")
        except Exception as e:
            st.error(f"Auto-fix run failed: {e}")
            
    # Run validation checks
    if check_clicked or fix_clicked:
        st.markdown("### 📊 Diagnostic Results")
        
        with st.spinner("Analyzing database constraints and constraints duplicates..."):
            results = validator.run_validation()
            
        if results is None:
            st.error("Could not run validation: Database connection unavailable.")
            return
            
        # Display cards
        total_issues = len(results.get("details", []))
        
        card1, card2, card3, card4 = st.columns(4)
        card1.metric("Duplicates (Players/Teams/Venues)", 
                     results["duplicate_players"] + results["duplicate_teams"] + results["duplicate_venues"])
        card2.metric("Missing Critical PKs/IDs", results["missing_ids"])
        card3.metric("Broken Foreign Keys", results["broken_foreign_keys"])
        card4.metric("Invalid Overs Formats", results["incorrect_overs_format"])
        
        # Display overall health status
        st.subheader("Diagnostic Status")
        if total_issues == 0:
            st.success("🎉 PASS: All database validation checks passed successfully!")
        elif results["broken_foreign_keys"] > 0 or results["missing_ids"] > 0:
            st.error(f"❌ CRITICAL ERROR: Database contains {total_issues} issues, including orphaned foreign keys or missing PKs.")
        else:
            st.warning(f"⚠️ WARNING: Database contains {total_issues} issues. Check details below.")
            
        # Detailed issues table
        if results["details"]:
            st.subheader("Details Logs")
            details_df = pd.DataFrame(results["details"])
            
            # Color coding rows based on severity
            def highlight_severity(row):
                color = 'transparent'
                if row['Severity'] == 'Critical':
                    color = '#ff4d4d'
                elif row['Severity'] == 'High':
                    color = '#ff944d'
                elif row['Severity'] == 'Medium':
                    color = '#ffff99'
                elif row['Severity'] == 'Warning':
                    color = '#e6e6e6'
                return [f'background-color: {color}' for _ in row]
                
            # Rename columns to look professional
            details_df.columns = ["Table", "Issue Type", "Description", "Severity"]
            
            st.dataframe(details_df, use_container_width=True)
            
            # Export reports option
            st.subheader("📥 Export Diagnostic Reports")
            
            # Generate reports files in background
            validator.generate_reports(results)
            
            # Download diagnostic reports directly from streamlit
            csv_report = details_df.to_csv(index=False)
            st.download_button(
                label="Download Validation Report as CSV 📥",
                data=csv_report,
                file_name="validation_report.csv",
                mime="text/csv"
            )
