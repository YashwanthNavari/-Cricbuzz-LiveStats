import streamlit as st
import time
import json
from api.client import CricbuzzClient
from api.matches import get_matches_list
from api.scorecard import get_match_scorecard
from api.players import get_player_info

def render_api_explorer():
    st.markdown("<h2 style='color: #1e90ff;'>🔌 API Explorer</h2>", unsafe_allow_html=True)
    st.write("Interact directly with live Cricbuzz RapidAPI endpoints. View latency, request logs, and raw response JSONs.")
    
    st.markdown("---")
    
    # Selection of endpoints
    endpoint_option = st.selectbox(
        "Choose Cricbuzz API Endpoint",
        [
            "Get Match List (live, recent, upcoming)",
            "Get Match Full Scorecard (hscard)",
            "Get Player Stats Profile"
        ]
    )
    
    # Render inputs based on selection
    params = {}
    match_id = None
    player_id = None
    match_type = "recent"
    
    if endpoint_option == "Get Match List (live, recent, upcoming)":
        match_type = st.radio("Select Match Category Filter", ["recent", "live", "upcoming"])
    elif endpoint_option == "Get Match Full Scorecard (hscard)":
        match_id = st.number_input("Match ID (e.g., 91689 for actual scorecards)", min_value=1, value=91689, step=1)
    elif endpoint_option == "Get Player Stats Profile":
        player_id = st.number_input("Player ID (e.g., 1413 for Virat Kohli)", min_value=1, value=1413, step=1)
        
    st.markdown("---")
    
    # Send Request Button
    send_btn = st.button("Send HTTP GET Request 🚀", use_container_width=True)
    
    if send_btn:
        st.subheader("📡 HTTP Transaction Logs")
        
        # Instantiate API Client
        try:
            client = CricbuzzClient()
            start_time = time.time()
            
            # Perform query based on type
            with st.spinner("Executing network fetch against Cricbuzz RapidAPI..."):
                if endpoint_option == "Get Match List (live, recent, upcoming)":
                    response_data = get_matches_list(client, match_type=match_type)
                    target_endpoint = f"/matches/v1/{match_type}"
                elif endpoint_option == "Get Match Full Scorecard (hscard)":
                    response_data = get_match_scorecard(client, match_id=match_id)
                    target_endpoint = f"/mcenter/v1/{match_id}/hscard"
                elif endpoint_option == "Get Player Stats Profile":
                    response_data = get_player_info(client, player_id=player_id)
                    target_endpoint = f"/stats/v1/player/{player_id}"
                    
            latency_ms = (time.time() - start_time) * 1000.0
            
            # Request metadata cards
            col1, col2, col3 = st.columns(3)
            col1.metric("API Response Status", "200 OK")
            col2.metric("Network Latency (ms)", f"{latency_ms:.2f} ms")
            col3.metric("RapidAPI Host", client.api_host)
            
            st.info(f"Target URL: `GET https://{client.api_host}{target_endpoint}`")
            
            # Formatted raw JSON display
            st.subheader("📄 Raw Response JSON Payload")
            st.json(response_data)
            
            # Download file option
            json_str = json.dumps(response_data, indent=2, ensure_ascii=False)
            st.download_button(
                label="Download JSON Payload 📥",
                data=json_str,
                file_name=f"cricbuzz_{endpoint_option.split()[1].lower()}.json",
                mime="application/json"
            )
            
        except Exception as e:
            st.error(f"HTTP Transaction failed or returned error code:")
            st.exception(e)
