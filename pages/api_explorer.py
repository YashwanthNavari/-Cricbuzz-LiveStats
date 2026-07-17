import os
import time
import json
import streamlit as st
from dotenv import load_dotenv
from api.client import CricbuzzClient
from api.matches import get_matches_list
from api.scorecard import get_match_scorecard
from api.players import get_player_info


def render_api_explorer():
    st.markdown(
        "<h2 style='color: #1e90ff;'>🔌 API Explorer</h2>", unsafe_allow_html=True
    )
    st.write(
        "Interact directly with live Cricbuzz RapidAPI endpoints. View latency, request logs, and raw response JSONs."
    )

    st.markdown("---")

    # Selection of endpoints
    endpoint_option = st.selectbox(
        "Choose Cricbuzz API Endpoint",
        [
            "Get Match List (live, recent, upcoming)",
            "Get Match Full Scorecard (hscard)",
            "Get Player Stats Profile",
        ],
    )

    # Render inputs based on selection
    params = {}
    match_id = None
    player_id = None
    match_type = "recent"

    if endpoint_option == "Get Match List (live, recent, upcoming)":
        match_type = st.radio(
            "Select Match Category Filter", ["recent", "live", "upcoming"]
        )
    elif endpoint_option == "Get Match Full Scorecard (hscard)":
        match_id = st.number_input(
            "Match ID (e.g., 91689 for actual scorecards)",
            min_value=1,
            value=91689,
            step=1,
        )
    elif endpoint_option == "Get Player Stats Profile":
        player_id = st.number_input(
            "Player ID (e.g., 1413 for Virat Kohli)", min_value=1, value=1413, step=1
        )

    st.markdown("---")

    # Send Request Button
    send_btn = st.button("Send HTTP GET Request 🚀", use_container_width=True)

    if send_btn:
        st.subheader("📡 HTTP Transaction Logs")

        # Check API key is configured before attempting network request
        load_dotenv()
        api_key = os.getenv("RAPIDAPI_KEY")
        if not api_key or api_key in ("your_rapidapi_key_here", ""):
            try:
                api_key = st.secrets.get("RAPIDAPI_KEY")
            except Exception:
                pass

        if not api_key or api_key in ("your_rapidapi_key_here", ""):
            st.warning("⚠️ **RAPIDAPI_KEY is not configured yet.**")
            st.markdown(
                """
                <div style='background:#1a202c;padding:20px;border-radius:10px;border-left:5px solid #f6ad55;margin-top:10px'>
                <h4 style='color:#f6ad55;margin-top:0'>🔑 How to add your API key</h4>
                <ol style='color:#cbd5e0;line-height:2'>
                <li>Get a free API key from <a href='https://rapidapi.com/cricbuzz/api/cricbuzz-cricket' target='_blank' style='color:#63b3ed'>RapidAPI → Cricbuzz Cricket</a></li>
                <li>Go to your Streamlit app's <b>Settings → Secrets</b> panel</li>
                <li>Add the following lines and click <b>Save</b>:</li>
                </ol>
                <pre style='background:#2d3748;padding:14px;border-radius:8px;color:#68d391'>
RAPIDAPI_KEY = "your_actual_key_here"
RAPIDAPI_HOST = "cricbuzz-cricket.p.rapidapi.com"
DATABASE_URL = "sqlite:///cricbuzz_db.sqlite"</pre>
                <p style='color:#a0aec0;margin-bottom:0'>The app will restart automatically once secrets are saved.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.stop()

        # Instantiate API Client and send request
        try:
            client = CricbuzzClient()
            start_time = time.time()

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

            col1, col2, col3 = st.columns(3)
            col1.metric("API Response Status", "200 OK ✅")
            col2.metric("Network Latency (ms)", f"{latency_ms:.2f} ms")
            col3.metric("RapidAPI Host", client.api_host)

            st.info(f"Target URL: `GET https://{client.api_host}{target_endpoint}`")

            st.subheader("📄 Raw Response JSON Payload")
            st.json(response_data)

            json_str = json.dumps(response_data, indent=2, ensure_ascii=False)
            st.download_button(
                label="Download JSON Payload 📥",
                data=json_str,
                file_name=f"cricbuzz_{endpoint_option.split()[1].lower()}.json",
                mime="application/json",
            )

        except Exception as e:
            err_msg = str(e)
            if "Max retries" in err_msg or "401" in err_msg or "403" in err_msg:
                st.error("❌ **API Request Failed**")
                st.markdown(
                    """
                    <div style='background:#1a202c;padding:20px;border-radius:10px;border-left:5px solid #fc8181'>
                    <h4 style='color:#fc8181;margin-top:0'>Possible causes</h4>
                    <ul style='color:#cbd5e0;line-height:1.9'>
                    <li>🔑 <b>Invalid API key</b> — double-check <code>RAPIDAPI_KEY</code> in your Streamlit Secrets.</li>
                    <li>📉 <b>Quota exceeded</b> — your free RapidAPI plan limit may be reached for today.</li>
                    <li>🌐 <b>Network timeout</b> — the Cricbuzz API may be temporarily unavailable.</li>
                    </ul>
                    <p style='color:#a0aec0;margin-bottom:0'>Technical error: <code>{}</code></p>
                    </div>
                    """.format(err_msg),
                    unsafe_allow_html=True,
                )
            else:
                st.error("❌ An unexpected error occurred.")
                st.exception(e)
