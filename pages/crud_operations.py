import streamlit as st
from sqlalchemy import text
from database.db import get_db


def render_crud_operations():
    st.markdown(
        "<h2 style='color: #1e90ff;'>🛠️ CRUD Operations</h2>", unsafe_allow_html=True
    )
    st.write(
        "Perform Create, Read, Update, and Delete operations on core cricket entities and review the raw SQL statements triggered."
    )

    st.markdown("---")

    tab_player, tab_team, tab_match, tab_series, tab_venue = st.tabs(
        ["🏃 Players", "👥 Teams", "🏏 Matches", "🏆 Series", "🏟️ Venues"]
    )

    # ------------------ PLAYERS TAB ------------------
    with tab_player:
        st.subheader("Player Record Management")
        action = st.radio(
            "Choose Action",
            ["Create Player", "Read/Update/Delete Player"],
            key="player_action",
        )

        if action == "Create Player":
            with st.form("create_player_form"):
                p_id = st.number_input("Player ID (Unique)", min_value=1, value=99999)
                p_name = st.text_input("Player Name")
                p_role = st.text_input("Role (e.g. Batsman, Bowler)")
                p_bat = st.text_input("Batting Style (e.g. Right-hand bat)")
                p_bowl = st.text_input("Bowling Style (e.g. Right-arm medium)")

                submitted = st.form_submit_button("Insert Record 📥")

                if submitted:
                    if not p_name:
                        st.error("Player Name is required!")
                    else:
                        sql_stmt = "INSERT INTO players (id, name, role, batting_style, bowling_style) VALUES (:id, :name, :role, :bat, :bowl)"
                        params = {
                            "id": p_id,
                            "name": p_name,
                            "role": p_role,
                            "bat": p_bat,
                            "bowl": p_bowl,
                        }

                        st.markdown("**SQL Executed:**")
                        st.code(
                            sql_stmt.replace(":id", str(p_id))
                            .replace(":name", f"'{p_name}'")
                            .replace(":role", f"'{p_role}'")
                            .replace(":bat", f"'{p_bat}'")
                            .replace(":bowl", f"'{p_bowl}'"),
                            language="sql",
                        )

                        try:
                            with get_db() as session:
                                session.execute(text(sql_stmt), params)
                                session.commit()
                            st.success("Player record inserted successfully!")
                            st.write("Affected Rows: 1")
                        except Exception as e:
                            st.error(f"Failed to insert record: {e}")

        elif action == "Read/Update/Delete Player":
            # Load players for selection
            players_list = []
            try:
                with get_db() as session:
                    res = session.execute(
                        text("SELECT id, name FROM players ORDER BY name")
                    ).fetchall()
                    players_list = [(r[0], f"{r[1]} (ID: {r[0]})") for r in res]
            except Exception:
                pass

            if not players_list:
                st.info("No players available to manage.")
            else:
                player_map = {label: val for val, label in players_list}
                sel_label = st.selectbox(
                    "Select Player Record", list(player_map.keys())
                )
                sel_id = player_map[sel_label]

                # Fetch details
                try:
                    with get_db() as session:
                        player_row = session.execute(
                            text("SELECT * FROM players WHERE id = :id"), {"id": sel_id}
                        ).fetchone()
                except Exception as e:
                    st.error(f"Failed to fetch details: {e}")
                    return

                if player_row:
                    with st.form("edit_player_form"):
                        st.write(f"Editing record for Player ID: **{sel_id}**")
                        edit_name = st.text_input("Name", value=player_row[1])
                        edit_role = st.text_input("Role", value=player_row[2] or "")
                        edit_bat = st.text_input(
                            "Batting Style", value=player_row[3] or ""
                        )
                        edit_bowl = st.text_input(
                            "Bowling Style", value=player_row[4] or ""
                        )

                        col_up, col_del = st.columns(2)
                        update_submit = col_up.form_submit_button("Update Player ⚡")
                        delete_submit = col_del.form_submit_button("Delete Player ❌")

                        if update_submit:
                            sql_stmt = "UPDATE players SET name = :name, role = :role, batting_style = :bat, bowling_style = :bowl WHERE id = :id"
                            params = {
                                "id": sel_id,
                                "name": edit_name,
                                "role": edit_role,
                                "bat": edit_bat,
                                "bowl": edit_bowl,
                            }

                            st.markdown("**SQL Executed:**")
                            st.code(
                                sql_stmt.replace(":id", str(sel_id))
                                .replace(":name", f"'{edit_name}'")
                                .replace(":role", f"'{edit_role}'")
                                .replace(":bat", f"'{edit_bat}'")
                                .replace(":bowl", f"'{edit_bowl}'"),
                                language="sql",
                            )

                            try:
                                with get_db() as session:
                                    session.execute(text(sql_stmt), params)
                                    session.commit()
                                st.success("Player record updated successfully!")
                                st.write("Affected Rows: 1")
                            except Exception as e:
                                st.error(f"Failed to update player: {e}")

                        if delete_submit:
                            sql_stmt = "DELETE FROM players WHERE id = :id"

                            st.markdown("**SQL Executed:**")
                            st.code(
                                sql_stmt.replace(":id", str(sel_id)), language="sql"
                            )

                            try:
                                with get_db() as session:
                                    session.execute(text(sql_stmt), {"id": sel_id})
                                    session.commit()
                                st.success("Player record deleted successfully!")
                                st.write("Affected Rows: 1")
                            except Exception as e:
                                st.error(
                                    f"Failed to delete player (Cascade rules apply): {e}"
                                )

    # ------------------ TEAMS TAB ------------------
    with tab_team:
        st.subheader("Team Record Management")
        t_action = st.radio(
            "Choose Action",
            ["Create Team", "Read/Update/Delete Team"],
            key="team_action",
        )

        if t_action == "Create Team":
            with st.form("create_team_form"):
                t_id = st.number_input("Team ID (Unique)", min_value=1, value=999)
                t_name = st.text_input("Team Name")
                t_sname = st.text_input("Short Name (e.g. IND, ENG)")

                submitted = st.form_submit_button("Insert Record 📥")

                if submitted:
                    if not t_name:
                        st.error("Team Name is required!")
                    else:
                        sql_stmt = "INSERT INTO teams (id, name, short_name) VALUES (:id, :name, :sname)"
                        params = {"id": t_id, "name": t_name, "sname": t_sname}

                        st.markdown("**SQL Executed:**")
                        st.code(
                            sql_stmt.replace(":id", str(t_id))
                            .replace(":name", f"'{t_name}'")
                            .replace(":sname", f"'{t_sname}'"),
                            language="sql",
                        )

                        try:
                            with get_db() as session:
                                session.execute(text(sql_stmt), params)
                                session.commit()
                            st.success("Team record inserted successfully!")
                            st.write("Affected Rows: 1")
                        except Exception as e:
                            st.error(f"Failed to insert record: {e}")

        elif t_action == "Read/Update/Delete Team":
            teams_list = []
            try:
                with get_db() as session:
                    res = session.execute(
                        text("SELECT id, name FROM teams ORDER BY name")
                    ).fetchall()
                    teams_list = [(r[0], f"{r[1]} (ID: {r[0]})") for r in res]
            except Exception:
                pass

            if not teams_list:
                st.info("No teams available to manage.")
            else:
                team_map = {label: val for val, label in teams_list}
                sel_label = st.selectbox("Select Team Record", list(team_map.keys()))
                sel_id = team_map[sel_label]

                try:
                    with get_db() as session:
                        team_row = session.execute(
                            text("SELECT * FROM teams WHERE id = :id"), {"id": sel_id}
                        ).fetchone()
                except Exception as e:
                    st.error(f"Failed to fetch details: {e}")
                    return

                if team_row:
                    with st.form("edit_team_form"):
                        st.write(f"Editing record for Team ID: **{sel_id}**")
                        edit_name = st.text_input("Name", value=team_row[1])
                        edit_sname = st.text_input(
                            "Short Name", value=team_row[2] or ""
                        )

                        col_up, col_del = st.columns(2)
                        update_submit = col_up.form_submit_button("Update Team ⚡")
                        delete_submit = col_del.form_submit_button("Delete Team ❌")

                        if update_submit:
                            sql_stmt = "UPDATE teams SET name = :name, short_name = :sname WHERE id = :id"
                            params = {
                                "id": sel_id,
                                "name": edit_name,
                                "sname": edit_sname,
                            }

                            st.markdown("**SQL Executed:**")
                            st.code(
                                sql_stmt.replace(":id", str(sel_id))
                                .replace(":name", f"'{edit_name}'")
                                .replace(":sname", f"'{edit_sname}'"),
                                language="sql",
                            )

                            try:
                                with get_db() as session:
                                    session.execute(text(sql_stmt), params)
                                    session.commit()
                                st.success("Team record updated successfully!")
                                st.write("Affected Rows: 1")
                            except Exception as e:
                                st.error(f"Failed to update team: {e}")

                        if delete_submit:
                            sql_stmt = "DELETE FROM teams WHERE id = :id"

                            st.markdown("**SQL Executed:**")
                            st.code(
                                sql_stmt.replace(":id", str(sel_id)), language="sql"
                            )

                            try:
                                with get_db() as session:
                                    session.execute(text(sql_stmt), {"id": sel_id})
                                    session.commit()
                                st.success("Team record deleted successfully!")
                                st.write("Affected Rows: 1")
                            except Exception as e:
                                st.error(
                                    f"Failed to delete team (Cascade rules apply): {e}"
                                )

    # ------------------ MATCHES TAB ------------------
    with tab_match:
        st.subheader("Match Record Management")
        st.info(
            "Match records reference Series, Venues, and Teams. Use the database viewer or cascade operations as required. Creating/Deleting matches is supported."
        )
        m_action = st.radio(
            "Choose Action", ["Create Match", "Delete Match"], key="match_action"
        )

        if m_action == "Create Match":
            # Load foreign keys lists
            series_opts = []
            venue_opts = []
            team_opts = []
            try:
                with get_db() as session:
                    res_s = session.execute(
                        text("SELECT id, name FROM series")
                    ).fetchall()
                    series_opts = [(r[0], r[1]) for r in res_s]
                    res_v = session.execute(
                        text("SELECT id, name FROM venues")
                    ).fetchall()
                    venue_opts = [(r[0], r[1]) for r in res_v]
                    res_t = session.execute(
                        text("SELECT id, name FROM teams")
                    ).fetchall()
                    team_opts = [(r[0], r[1]) for r in res_t]
            except Exception:
                pass

            if not team_opts:
                st.warning("Teams list is empty. Add teams before registering a match.")
            else:
                with st.form("create_match_form"):
                    m_id = st.number_input("Match ID (Unique)", min_value=1, value=9999)
                    m_desc = st.text_input("Match Description (e.g. Final, Match 1)")
                    m_format = st.selectbox("Format", ["T20", "ODI", "Test", "Other"])
                    m_status = st.text_input("Status (e.g. Live, Complete)")

                    m_series = st.selectbox(
                        "Select Series",
                        [None] + [s[0] for s in series_opts],
                        format_func=lambda x: dict(series_opts).get(x, "None"),
                    )
                    m_venue = st.selectbox(
                        "Select Venue",
                        [None] + [v[0] for v in venue_opts],
                        format_func=lambda x: dict(venue_opts).get(x, "None"),
                    )

                    m_t1 = st.selectbox(
                        "Team 1",
                        [t[0] for t in team_opts],
                        format_func=lambda x: dict(team_opts).get(x),
                    )
                    m_t2 = st.selectbox(
                        "Team 2",
                        [t[0] for t in team_opts],
                        format_func=lambda x: dict(team_opts).get(x),
                        index=min(1, len(team_opts) - 1),
                    )

                    overs_lim = st.number_input("Overs Limit", min_value=1, value=20)

                    submitted = st.form_submit_button("Register Match 🏏")

                    if submitted:
                        sql_stmt = """
                        INSERT INTO matches (id, series_id, venue_id, match_desc, format, status, team1_id, team2_id, match_overs_limit, is_live, is_completed) 
                        VALUES (:id, :series_id, :venue_id, :desc, :format, :status, :team1, :team2, :overs_lim, 0, 1)
                        """
                        params = {
                            "id": m_id,
                            "series_id": m_series,
                            "venue_id": m_venue,
                            "desc": m_desc,
                            "format": m_format,
                            "status": m_status,
                            "team1": m_t1,
                            "team2": m_t2,
                            "overs_lim": overs_lim,
                        }

                        st.markdown("**SQL Executed:**")
                        st.code(
                            sql_stmt.replace(":id", str(m_id))
                            .replace(":series_id", str(m_series))
                            .replace(":venue_id", str(m_venue))
                            .replace(":desc", f"'{m_desc}'")
                            .replace(":format", f"'{m_format}'")
                            .replace(":status", f"'{m_status}'")
                            .replace(":team1", str(m_t1))
                            .replace(":team2", str(m_t2))
                            .replace(":overs_lim", str(overs_lim)),
                            language="sql",
                        )

                        try:
                            with get_db() as session:
                                session.execute(text(sql_stmt), params)
                                session.commit()
                            st.success("Match record registered successfully!")
                            st.write("Affected Rows: 1")
                        except Exception as e:
                            st.error(f"Failed to register match: {e}")

        elif m_action == "Delete Match":
            matches_opts = []
            try:
                with get_db() as session:
                    res = session.execute(
                        text("SELECT id, match_desc FROM matches")
                    ).fetchall()
                    matches_opts = [(r[0], f"Match ID: {r[0]} ({r[1]})") for r in res]
            except Exception:
                pass

            if not matches_opts:
                st.info("No matches available in database.")
            else:
                m_map = {label: val for val, label in matches_opts}
                sel_label = st.selectbox("Select Match to Delete", list(m_map.keys()))
                sel_id = m_map[sel_label]

                delete_btn = st.button("Confirm Delete Match Record ❌")
                if delete_btn:
                    sql_stmt = "DELETE FROM matches WHERE id = :id"

                    st.markdown("**SQL Executed:**")
                    st.code(sql_stmt.replace(":id", str(sel_id)), language="sql")

                    try:
                        with get_db() as session:
                            session.execute(text(sql_stmt), {"id": sel_id})
                            session.commit()
                        st.success(
                            "Match deleted successfully (innings and scorecard details cascadingly removed)."
                        )
                        st.write("Affected Rows: 1")
                    except Exception as e:
                        st.error(f"Delete failed: {e}")

    # ------------------ SERIES TAB ------------------
    with tab_series:
        st.subheader("Series Record Management")
        s_action = st.radio(
            "Choose Action", ["Create Series", "Delete Series"], key="series_action"
        )

        if s_action == "Create Series":
            with st.form("create_series_form"):
                s_id = st.number_input("Series ID (Unique)", min_value=1, value=9999)
                s_name = st.text_input("Series Name")
                s_type = st.text_input("Series Type (e.g. International, League)")

                submitted = st.form_submit_button("Insert Record 📥")

                if submitted:
                    if not s_name:
                        st.error("Series Name is required!")
                    else:
                        sql_stmt = "INSERT INTO series (id, name, series_type) VALUES (:id, :name, :type)"
                        params = {"id": s_id, "name": s_name, "type": s_type}

                        st.markdown("**SQL Executed:**")
                        st.code(
                            sql_stmt.replace(":id", str(s_id))
                            .replace(":name", f"'{s_name}'")
                            .replace(":type", f"'{s_type}'"),
                            language="sql",
                        )

                        try:
                            with get_db() as session:
                                session.execute(text(sql_stmt), params)
                                session.commit()
                            st.success("Series record inserted successfully!")
                            st.write("Affected Rows: 1")
                        except Exception as e:
                            st.error(f"Failed to insert series: {e}")

        elif s_action == "Delete Series":
            series_opts = []
            try:
                with get_db() as session:
                    res = session.execute(
                        text("SELECT id, name FROM series")
                    ).fetchall()
                    series_opts = [(r[0], f"ID: {r[0]} ({r[1]})") for r in res]
            except Exception:
                pass

            if not series_opts:
                st.info("No series records found.")
            else:
                s_map = {label: val for val, label in series_opts}
                sel_label = st.selectbox("Select Series to Delete", list(s_map.keys()))
                sel_id = s_map[sel_label]

                delete_btn = st.button("Delete Series Record ❌")
                if delete_btn:
                    sql_stmt = "DELETE FROM series WHERE id = :id"

                    st.markdown("**SQL Executed:**")
                    st.code(sql_stmt.replace(":id", str(sel_id)), language="sql")

                    try:
                        with get_db() as session:
                            session.execute(text(sql_stmt), {"id": sel_id})
                            session.commit()
                        st.success("Series record deleted successfully.")
                        st.write("Affected Rows: 1")
                    except Exception as e:
                        st.error(f"Delete failed: {e}")

    # ------------------ VENUES TAB ------------------
    with tab_venue:
        st.subheader("Venue Record Management")
        v_action = st.radio(
            "Choose Action", ["Create Venue", "Delete Venue"], key="venue_action"
        )

        if v_action == "Create Venue":
            with st.form("create_venue_form"):
                v_id = st.number_input("Venue ID (Unique)", min_value=1, value=999)
                v_name = st.text_input("Venue Name")
                v_city = st.text_input("City")
                v_country = st.text_input("Country")
                v_capacity = st.number_input("Capacity", min_value=0, value=25000)

                submitted = st.form_submit_button("Insert Record 📥")

                if submitted:
                    if not v_name:
                        st.error("Venue Name is required!")
                    else:
                        sql_stmt = "INSERT INTO venues (id, name, city, country, capacity) VALUES (:id, :name, :city, :country, :capacity)"
                        params = {
                            "id": v_id,
                            "name": v_name,
                            "city": v_city,
                            "country": v_country,
                            "capacity": v_capacity,
                        }

                        st.markdown("**SQL Executed:**")
                        st.code(
                            sql_stmt.replace(":id", str(v_id))
                            .replace(":name", f"'{v_name}'")
                            .replace(":city", f"'{v_city}'")
                            .replace(":country", f"'{v_country}'")
                            .replace(":capacity", str(v_capacity)),
                            language="sql",
                        )

                        try:
                            with get_db() as session:
                                session.execute(text(sql_stmt), params)
                                session.commit()
                            st.success("Venue record inserted successfully!")
                            st.write("Affected Rows: 1")
                        except Exception as e:
                            st.error(f"Failed to insert venue: {e}")

        elif v_action == "Delete Venue":
            venue_opts = []
            try:
                with get_db() as session:
                    res = session.execute(
                        text("SELECT id, name FROM venues")
                    ).fetchall()
                    venue_opts = [(r[0], f"ID: {r[0]} ({r[1]})") for r in res]
            except Exception:
                pass

            if not venue_opts:
                st.info("No venues found in database.")
            else:
                v_map = {label: val for val, label in venue_opts}
                sel_label = st.selectbox("Select Venue to Delete", list(v_map.keys()))
                sel_id = v_map[sel_label]

                delete_btn = st.button("Delete Venue Record ❌")
                if delete_btn:
                    sql_stmt = "DELETE FROM venues WHERE id = :id"

                    st.markdown("**SQL Executed:**")
                    st.code(sql_stmt.replace(":id", str(sel_id)), language="sql")

                    try:
                        with get_db() as session:
                            session.execute(text(sql_stmt), {"id": sel_id})
                            session.commit()
                        st.success("Venue record deleted successfully.")
                        st.write("Affected Rows: 1")
                    except Exception as e:
                        st.error(f"Delete failed: {e}")
