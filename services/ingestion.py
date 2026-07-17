import os
import time
import logging
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from tqdm import tqdm
from sqlalchemy.orm import Session

from api.client import CricbuzzClient
from api.matches import get_matches_list
from api.scorecard import get_match_scorecard
from database.db import get_db
from database.models import (
    Series,
    Venue,
    Team,
    Player,
    Match,
    Innings,
    BattingScore,
    BowlingScore,
    FieldingRecord,
    Partnership,
)
from services.validator import validate_matches_json, validate_scorecard_json
from services.transformer import (
    transform_series,
    transform_venue,
    transform_team,
    transform_match,
    transform_scorecard,
    extract_players_from_scorecard,
)

logger = logging.getLogger("IngestionPipeline")


class IngestionPipeline:
    """
    Automated ingestion pipeline.
    Downloads matches list, walks matches, upserts structural tables,
    fetches scorecards, tracks progress, handles resume states, and generates reports.
    """

    def __init__(self, client: Optional[CricbuzzClient] = None) -> None:
        self.client = client or CricbuzzClient()
        self.workspace_root: Path = self.client.workspace_root
        self.reports_dir: Path = self.workspace_root / "processed_data" / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def _upsert_series(self, session: Session, series: Series) -> Series:
        existing = session.get(Series, series.id)
        if existing:
            existing.name = series.name
            if series.start_date:
                existing.start_date = series.start_date
            if series.end_date:
                existing.end_date = series.end_date
            if series.series_type:
                existing.series_type = series.series_type
            return existing
        session.add(series)
        return series

    def _upsert_venue(self, session: Session, venue: Venue) -> Venue:
        if venue.id is None:
            existing = (
                session.query(Venue).filter_by(name=venue.name, city=venue.city).first()
            )
            if existing:
                return existing
            session.add(venue)
            session.flush()
            return venue

        existing = session.get(Venue, venue.id)
        if existing:
            existing.name = venue.name
            if venue.city:
                existing.city = venue.city
            if venue.country:
                existing.country = venue.country
            if venue.capacity:
                existing.capacity = venue.capacity
            return existing
        session.add(venue)
        return venue

    def _upsert_team(self, session: Session, team: Team) -> Team:
        existing = session.get(Team, team.id)
        if existing:
            existing.name = team.name
            if team.short_name:
                existing.short_name = team.short_name
            return existing
        session.add(team)
        return team

    def _upsert_player(self, session: Session, player: Player) -> Player:
        existing = session.get(Player, player.id)
        if existing:
            existing.name = player.name
            if player.role:
                existing.role = player.role
            if player.batting_style:
                existing.batting_style = player.batting_style
            if player.bowling_style:
                existing.bowling_style = player.bowling_style
            if player.image_url:
                existing.image_url = player.image_url
            return existing
        session.add(player)
        return player

    def _upsert_match(self, session: Session, match: Match) -> Match:
        existing = session.get(Match, match.id)
        if existing:
            existing.series_id = match.series_id
            existing.venue_id = match.venue_id
            existing.match_desc = match.match_desc
            existing.format = match.format
            existing.status = match.status
            existing.team1_id = match.team1_id
            existing.team2_id = match.team2_id
            existing.toss_winner_id = match.toss_winner_id
            existing.toss_decision = match.toss_decision
            existing.winner_id = match.winner_id
            existing.match_start_time = match.match_start_time
            existing.is_live = match.is_live
            existing.is_completed = match.is_completed
            return existing
        session.add(match)
        return match

    def is_scorecard_ingested(self, match_id: int) -> bool:
        """Helper to determine if a scorecard has already been completed in database (Resume support)."""
        try:
            with get_db() as session:
                # Check if there are any innings records for this match ID
                count = session.query(Innings).filter_by(match_id=match_id).count()
                return count > 0
        except Exception as e:
            logger.warning(f"Error checking DB for match {match_id} status: {e}")
            return False

    def ingest_matches_list(self, match_type: str = "recent") -> Dict[str, Any]:
        """
        Main pipeline orchestrator. Fetches matches, processes them with progress bars,
        checks DB state for resume capabilities, runs transactions, and writes an execution report.
        """
        start_time = time.time()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        logger.info(f"Starting database ingestion run. Type: {match_type}")

        # Fetch matches from client
        try:
            raw_response = get_matches_list(self.client, match_type)
        except Exception as e:
            logger.critical(f"Failed to retrieve match listings from API: {e}")
            return {"status": "failed", "error": str(e)}

        if not validate_matches_json(raw_response):
            logger.critical(
                "Matches list structural validation failed. Aborting database run."
            )
            return {"status": "failed", "error": "validation_failed"}

        # Collect all matches to process
        flat_matches_to_process = []
        type_matches = raw_response.get("typeMatches", [])
        for tm in type_matches:
            for sm in tm.get("seriesMatches", []):
                series_wrapper = sm.get("seriesAdWrapper")
                if not series_wrapper:
                    continue
                series_id = series_wrapper.get("seriesId")
                series_name = series_wrapper.get("seriesName")
                for m_data in series_wrapper.get("matches", []):
                    match_info = m_data.get("matchInfo")
                    if match_info:
                        flat_matches_to_process.append(
                            {
                                "series_id": series_id,
                                "series_name": series_name,
                                "match_data": m_data,
                                "match_info": match_info,
                            }
                        )

        total_found = len(flat_matches_to_process)
        matches_ingested = 0
        scorecards_fetched = 0
        scorecards_skipped = 0
        errors_encountered = 0
        detailed_errors = []

        logger.info(
            f"Discovered {total_found} matches to ingest. Beginning processing..."
        )

        # Process matches with a terminal progress bar (tqdm)
        for item in tqdm(
            flat_matches_to_process, desc="Ingesting Matches", unit="match"
        ):
            series_id = item["series_id"]
            series_name = item["series_name"]
            m_data = item["match_data"]
            match_info = item["match_info"]
            match_id = match_info["matchId"]
            state = match_info.get("state") or match_info.get("matchState", "")

            # Determine live and complete states
            is_live = state.lower() == "live"
            is_completed = state.lower() == "complete"

            try:
                # 1. Structural entities insertion / updates (Series, Venues, Teams, Match details)
                with get_db() as session:
                    # Series
                    series_obj = Series(id=series_id, name=series_name)
                    self._upsert_series(session, series_obj)

                    # Venue
                    venue_data = match_info.get("venueInfo")
                    if venue_data and venue_data.get("id"):
                        venue_obj = transform_venue(venue_data)
                        self._upsert_venue(session, venue_obj)

                    # Teams
                    t1 = transform_team(match_info["team1"])
                    t2 = transform_team(match_info["team2"])
                    self._upsert_team(session, t1)
                    self._upsert_team(session, t2)

                    # Match
                    match_obj = transform_match(m_data, series_id=series_id)
                    match_obj.is_live = is_live
                    match_obj.is_completed = is_completed
                    self._upsert_match(session, match_obj)

                    session.flush()
                    matches_ingested += 1

                # 2. Scorecard Ingestion (Only for completed matches)
                if is_completed:
                    # Resume logic: Check if scorecard is already in DB
                    if self.is_scorecard_ingested(match_id):
                        logger.info(
                            f"Match {match_id} scorecard already exists in DB. Skipping API download."
                        )
                        scorecards_skipped += 1
                    else:
                        success = self.ingest_scorecard(match_id)
                        if success:
                            scorecards_fetched += 1
                        else:
                            errors_encountered += 1
                            detailed_errors.append(
                                f"Match {match_id}: Scorecard ingestion failed."
                            )

            except Exception as e:
                logger.error(f"Failed to ingest match {match_id} details: {e}")
                errors_encountered += 1
                detailed_errors.append(f"Match {match_id}: {str(e)}")

        # Calculate run summary
        duration = time.time() - start_time
        report = {
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "match_type": match_type,
            "duration_seconds": round(duration, 2),
            "total_matches_discovered": total_found,
            "matches_ingested": matches_ingested,
            "scorecards_fetched_api": scorecards_fetched,
            "scorecards_skipped_db_resume": scorecards_skipped,
            "errors_encountered": errors_encountered,
            "scorecards_ingested": scorecards_fetched,
            "errors": errors_encountered,
            "error_details": detailed_errors,
        }

        # Write execution report to file
        report_file = self.reports_dir / f"ingestion_report_{timestamp}.json"
        try:
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(
                f"Ingestion run report generated: processed_data/reports/ingestion_report_{timestamp}.json"
            )
        except Exception as e:
            logger.error(f"Failed to save ingestion report: {e}")

        return report

    def ingest_scorecard(self, match_id: int) -> bool:
        """
        Downloads detailed scorecard, validates JSON structure,
        upserts players, and updates innings and batting/bowling/fielding statistics.
        """
        logger.info(f"Downloading scorecard for Match: {match_id}")
        try:
            raw_scorecard = get_match_scorecard(self.client, match_id)
        except Exception as e:
            logger.error(
                f"Network error downloading scorecard for Match {match_id}: {e}"
            )
            return False

        if not validate_scorecard_json(raw_scorecard):
            logger.error(
                f"Downloaded scorecard structural validation failed for Match {match_id}"
            )
            return False

        try:
            with get_db() as session:
                # 1. Confirm Match exists
                match_ref = session.get(Match, match_id)
                if not match_ref:
                    logger.error(
                        f"Match ID {match_id} does not exist in DB. Cannot attach scorecard."
                    )
                    return False

                # 2. Extract and Upsert Players
                players = extract_players_from_scorecard(raw_scorecard)
                for player in players:
                    self._upsert_player(session, player)
                session.flush()

                # Construct team name mappings to resolve IDs
                team_name_to_id = {
                    match_ref.team1.name.lower().strip(): match_ref.team1_id,
                    match_ref.team2.name.lower().strip(): match_ref.team2_id,
                }
                if match_ref.team1.short_name:
                    team_name_to_id[match_ref.team1.short_name.lower().strip()] = (
                        match_ref.team1_id
                    )
                if match_ref.team2.short_name:
                    team_name_to_id[match_ref.team2.short_name.lower().strip()] = (
                        match_ref.team2_id
                    )

                # 3. Transform Scorecard Innings & Scores
                innings_list = transform_scorecard(
                    raw_scorecard,
                    match_id=match_id,
                    team1_id=match_ref.team1_id,
                    team2_id=match_ref.team2_id,
                    team_name_to_id=team_name_to_id,
                )

                # 4. Upsert Innings & Scores
                for inning in innings_list:
                    # Check existing Innings
                    existing_inn = (
                        session.query(Innings)
                        .filter_by(match_id=match_id, innings_num=inning.innings_num)
                        .first()
                    )

                    if existing_inn:
                        # Update innings metrics
                        existing_inn.runs = inning.runs
                        existing_inn.wickets = inning.wickets
                        existing_inn.overs = inning.overs

                        # Delete old children (Batting, Bowling, Fielding, Partnerships) to clean overwrite
                        session.query(BattingScore).filter_by(
                            innings_id=existing_inn.id
                        ).delete()
                        session.query(BowlingScore).filter_by(
                            innings_id=existing_inn.id
                        ).delete()
                        session.query(FieldingRecord).filter_by(
                            innings_id=existing_inn.id
                        ).delete()
                        session.query(Partnership).filter_by(
                            innings_id=existing_inn.id
                        ).delete()
                        session.flush()

                        target_inn_id = existing_inn.id
                    else:
                        session.add(inning)
                        session.flush()
                        target_inn_id = inning.id

                    # Re-populate scores
                    fielding_map = {}
                    for bat in inning.batting_scores:
                        bat.innings_id = target_inn_id
                        session.add(bat)

                        # Populate aggregated fielding record for involved fielder
                        if bat.fielder_id and bat.dismissal_type:
                            is_catch = bat.dismissal_type.lower() == "caught"
                            is_stumping = bat.dismissal_type.lower() == "stumped"
                            is_runout = bat.dismissal_type.lower() == "run out"

                            if not (is_catch or is_stumping or is_runout):
                                continue

                            f_id = bat.fielder_id
                            if f_id in fielding_map:
                                fr = fielding_map[f_id]
                                if is_catch:
                                    fr.catches += 1
                                elif is_stumping:
                                    fr.stumpings += 1
                                elif is_runout:
                                    fr.run_outs += 1
                            else:
                                # Check if it already exists in database
                                fr = (
                                    session.query(FieldingRecord)
                                    .filter_by(innings_id=target_inn_id, player_id=f_id)
                                    .first()
                                )

                                if fr:
                                    if is_catch:
                                        fr.catches += 1
                                    elif is_stumping:
                                        fr.stumpings += 1
                                    elif is_runout:
                                        fr.run_outs += 1
                                else:
                                    fr = FieldingRecord(
                                        innings_id=target_inn_id,
                                        player_id=f_id,
                                        catches=1 if is_catch else 0,
                                        stumpings=1 if is_stumping else 0,
                                        run_outs=1 if is_runout else 0,
                                    )
                                    session.add(fr)
                                fielding_map[f_id] = fr

                    for bowl in inning.bowling_scores:
                        bowl.innings_id = target_inn_id
                        session.add(bowl)

                # Programmatic Player of the Match determination
                winner_team_id = match_ref.winner_id
                potm_player_id = None
                best_score = -1.0

                player_performance = {}
                for inn in innings_list:
                    # batsman scores
                    for bat in inn.batting_scores:
                        pid = bat.player_id
                        p_team = inn.batting_team_id
                        player_performance.setdefault(
                            pid, {"team": p_team, "score": 0.0}
                        )
                        player_performance[pid]["score"] += float(bat.runs)
                    # bowler scores
                    for bowl in inn.bowling_scores:
                        pid = bowl.player_id
                        p_team = inn.bowling_team_id
                        player_performance.setdefault(
                            pid, {"team": p_team, "score": 0.0}
                        )
                        player_performance[pid]["score"] += float(bowl.wickets) * 25.0

                # Filter by winning team if available
                candidates = []
                if winner_team_id:
                    candidates = [
                        (pid, info)
                        for pid, info in player_performance.items()
                        if info["team"] == winner_team_id
                    ]

                if not candidates:
                    candidates = list(player_performance.items())

                for pid, info in candidates:
                    if info["score"] > best_score:
                        best_score = info["score"]
                        potm_player_id = pid

                if potm_player_id:
                    match_ref.player_of_the_match_id = potm_player_id
                    logger.info(
                        f"Calculated Player of the Match for Match {match_id}: Player ID {potm_player_id} (Score: {best_score})"
                    )

                logger.info(
                    f"Successfully processed and stored scorecard for Match {match_id}"
                )
                return True

        except Exception as e:
            logger.error(
                f"Database transaction error processing scorecard for Match {match_id}: {e}"
            )
            return False
