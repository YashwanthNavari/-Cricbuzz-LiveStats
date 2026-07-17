import os
import unittest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.client import CricbuzzClient
from services.validator import validate_matches_json, validate_scorecard_json, validate_player_json
from services.transformer import (
    transform_series, transform_venue, transform_team, transform_match,
    transform_scorecard, extract_players_from_scorecard
)
from services.ingestion import IngestionPipeline
from database.models import Base, Series, Venue, Team, Match, Innings, BattingScore, BowlingScore, Player

class TestCricbuzzClient(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch("requests.Session.request")
    def test_client_request_success_and_save(self, mock_request):
        # Setup mocks
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_request.return_value = mock_response

        # Instantiate client with patched dirs
        client = CricbuzzClient()
        client.raw_data_dir = Path(self.test_dir) / "raw_data"
        client.raw_data_dir.mkdir(parents=True, exist_ok=True)

        res = client.request("matches/v1/recent")
        self.assertEqual(res, {"status": "ok"})
        mock_request.assert_called_once()
        
        # Verify that response is saved
        subdirs = list(client.raw_data_dir.glob("matches_v1_recent/*"))
        self.assertEqual(len(subdirs), 1)
        with open(subdirs[0], "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data, {"status": "ok"})

    @patch("requests.Session.request")
    @patch("time.sleep")
    def test_client_rate_limiting_retry(self, mock_sleep, mock_request):
        # 1st call rate limit, 2nd call success
        mock_response_limit = MagicMock()
        mock_response_limit.status_code = 429
        mock_response_limit.headers = {"Retry-After": "1"}

        mock_response_ok = MagicMock()
        mock_response_ok.status_code = 200
        mock_response_ok.json.return_value = {"success": True}

        mock_request.side_effect = [mock_response_limit, mock_response_ok]

        client = CricbuzzClient()
        client.raw_data_dir = Path(self.test_dir) / "raw_data"
        client.raw_data_dir.mkdir(parents=True, exist_ok=True)

        res = client.request("matches/v1/recent", max_retries=2, backoff_factor=1.0)
        self.assertEqual(res, {"success": True})
        self.assertEqual(mock_request.call_count, 2)
        mock_sleep.assert_called_with(1)

class TestValidator(unittest.TestCase):
    def setUp(self):
        self.valid_matches_data = {
            "typeMatches": [
                {
                    "matchType": "International",
                    "seriesMatches": [
                        {
                            "seriesAdWrapper": {
                                "seriesId": 3813,
                                "seriesName": "ICC Men's T20 World Cup 2026",
                                "matches": [
                                    {
                                        "matchInfo": {
                                            "matchId": 89452,
                                            "matchDescription": "Final",
                                            "matchFormat": "T20",
                                            "matchState": "Complete",
                                            "status": "India won by 7 runs",
                                            "team1": { "teamId": 2, "teamName": "India", "teamSName": "IND" },
                                            "team2": { "teamId": 9, "teamName": "South Africa", "teamSName": "RSA" },
                                            "venueInfo": { "id": 12, "name": "Kensington Oval", "city": "Bridgetown", "country": "Barbados" }
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        
        self.valid_scorecard_data = {
            "scorecard": [
                {
                    "inningsid": 1,
                    "batteamname": "India",
                    "batteamsname": "IND",
                    "score": 176,
                    "wickets": 7,
                    "overs": 20.0,
                    "batsman": [
                        {
                            "id": 101,
                            "runs": 76,
                            "balls": 59,
                            "fours": 6,
                            "sixes": 2,
                            "strkrate": "128.81",
                            "outdec": "c Jansen b Maharaj"
                        }
                    ],
                    "bowler": [
                        {
                            "id": 201,
                            "overs": "4.0",
                            "maidens": 0,
                            "runs": 26,
                            "wickets": 2,
                            "economy": "6.5"
                        }
                    ]
                }
            ]
        }

    def test_validate_matches_success(self):
        self.assertTrue(validate_matches_json(self.valid_matches_data))

    def test_validate_scorecard_success(self):
        self.assertTrue(validate_scorecard_json(self.valid_scorecard_data))

    def test_validate_invalid_scorecard_fails(self):
        invalid_data = {"matchId": 89452}  # Missing scorecard key
        self.assertFalse(validate_scorecard_json(invalid_data))

class TestTransformer(unittest.TestCase):
    def test_transformations(self):
        series_data = {
            "seriesId": 123,
            "seriesName": "IPL 2026",
            "startDate": "1719673200000",
            "endDate": "1719673200000",
            "seriesType": "League"
        }
        series = transform_series(series_data)
        self.assertEqual(series.id, 123)
        self.assertEqual(series.name, "IPL 2026")
        self.assertEqual(series.series_type, "League")

        team_data = { "teamId": 2, "teamName": "India", "teamSName": "IND" }
        team = transform_team(team_data)
        self.assertEqual(team.id, 2)
        self.assertEqual(team.name, "India")
        self.assertEqual(team.short_name, "IND")

        venue_data = { "id": 12, "name": "Wankhede", "city": "Mumbai", "country": "India" }
        venue = transform_venue(venue_data)
        self.assertEqual(venue.id, 12)
        self.assertEqual(venue.name, "Wankhede")

        match_raw = {
            "matchInfo": {
                "matchId": 999,
                "matchDescription": "Match 1",
                "matchFormat": "T20",
                "team1": { "teamId": 1, "teamName": "Team A" },
                "team2": { "teamId": 2, "teamName": "Team B" }
            }
        }
        match = transform_match(match_raw, series_id=123)
        self.assertEqual(match.id, 999)
        self.assertEqual(match.series_id, 123)
        self.assertEqual(match.team1_id, 1)

class TestIngestionPipeline(unittest.TestCase):
    def setUp(self):
        from sqlalchemy.pool import StaticPool
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Patch get_db to return our in-memory SQLite database session
        self.db_patcher = patch("services.ingestion.get_db")
        self.mock_get_db = self.db_patcher.start()
        
        from contextlib import contextmanager
        
        @contextmanager
        def mock_db_ctx():
            session = self.SessionLocal()
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
        
        self.mock_get_db.side_effect = mock_db_ctx

    def tearDown(self):
        self.db_patcher.stop()

    @patch("services.ingestion.get_matches_list")
    @patch("services.ingestion.get_match_scorecard")
    def test_pipeline_ingestion(self, mock_scorecard, mock_matches):
        # Mock match list response
        mock_matches.return_value = {
            "typeMatches": [
                {
                    "matchType": "International",
                    "seriesMatches": [
                        {
                            "seriesAdWrapper": {
                                "seriesId": 3813,
                                "seriesName": "T20 WC 2026",
                                "matches": [
                                    {
                                        "matchInfo": {
                                            "matchId": 89452,
                                            "matchDescription": "Final",
                                            "matchFormat": "T20",
                                            "matchState": "Complete",
                                            "status": "India won by 7 runs",
                                            "team1": { "teamId": 2, "teamName": "India", "teamSName": "IND" },
                                            "team2": { "teamId": 9, "teamName": "South Africa", "teamSName": "RSA" },
                                            "venueInfo": { "id": 12, "name": "Kensington Oval", "city": "Bridgetown", "country": "Barbados" }
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        # Mock scorecard response
        mock_scorecard.return_value = {
            "scorecard": [
                {
                    "inningsid": 1,
                    "batteamname": "India",
                    "batteamsname": "IND",
                    "score": 176,
                    "wickets": 7,
                    "overs": 20.0,
                    "batsman": [
                        {
                            "id": 101,
                            "name": "Virat Kohli",
                            "runs": 76,
                            "balls": 59,
                            "fours": 6,
                            "sixes": 2,
                            "strkrate": "128.81",
                            "outdec": "c Jansen b Maharaj"
                        }
                    ],
                    "bowler": [
                        {
                            "id": 201,
                            "name": "Anrich Nortje",
                            "overs": "4.0",
                            "maidens": 0,
                            "runs": 26,
                            "wickets": 2,
                            "economy": "6.5"
                        }
                    ]
                }
            ]
        }

        pipeline = IngestionPipeline()
        results = pipeline.ingest_matches_list(match_type="recent")
        
        # Verify ingestion summary results
        self.assertEqual(results["status"], "success")
        self.assertEqual(results["matches_ingested"], 1)
        self.assertEqual(results["scorecards_fetched_api"], 1)
        self.assertEqual(results["scorecards_ingested"], 1)
        self.assertEqual(results["errors_encountered"], 0)
        self.assertEqual(results["errors"], 0)

        # Inspect SQLite contents to verify insertion and database models relationships
        session = self.SessionLocal()
        
        # 1. Matches
        matches = session.query(Match).all()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].id, 89452)
        self.assertEqual(matches[0].venue_id, 12)
        self.assertEqual(matches[0].series_id, 3813)
        
        # 2. Teams
        teams = session.query(Team).all()
        self.assertEqual(len(teams), 2)
        team_ids = [t.id for t in teams]
        self.assertIn(2, team_ids)
        self.assertIn(9, team_ids)

        # 3. Series
        series = session.query(Series).all()
        self.assertEqual(len(series), 1)
        self.assertEqual(series[0].name, "T20 WC 2026")

        # 4. Venues
        venues = session.query(Venue).all()
        self.assertEqual(len(venues), 1)
        self.assertEqual(venues[0].name, "Kensington Oval")

        # 5. Players
        players = session.query(Player).all()
        self.assertEqual(len(players), 2)
        player_names = [p.name for p in players]
        self.assertIn("Virat Kohli", player_names)
        self.assertIn("Anrich Nortje", player_names)

        # 6. Innings
        innings = session.query(Innings).all()
        self.assertEqual(len(innings), 1)
        self.assertEqual(innings[0].runs, 176)
        self.assertEqual(innings[0].wickets, 7)

        # 7. Batting scores
        batting_scores = session.query(BattingScore).all()
        self.assertEqual(len(batting_scores), 1)
        self.assertEqual(batting_scores[0].runs, 76)
        self.assertEqual(batting_scores[0].player_id, 101)

        # 8. Bowling scores
        bowling_scores = session.query(BowlingScore).all()
        self.assertEqual(len(bowling_scores), 1)
        self.assertEqual(bowling_scores[0].wickets, 2)
        self.assertEqual(bowling_scores[0].player_id, 201)

        session.close()

if __name__ == "__main__":
    unittest.main()
