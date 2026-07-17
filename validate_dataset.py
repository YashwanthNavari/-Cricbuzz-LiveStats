import os
import sys
import csv
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Any
from dotenv import load_dotenv
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session

# Ensure workspace is in python path
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

from database.db import get_db, get_engine
from database.models import (
    Player,
    Team,
    Venue,
    Match,
    Innings,
    BattingScore,
    BowlingScore,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] Validator: %(message)s"
)
logger = logging.getLogger("DatasetValidator")


class DatasetValidator:
    def __init__(self) -> None:
        load_dotenv()
        self.workspace_root = Path(__file__).resolve().parent
        self.reports_dir = self.workspace_root / "processed_data" / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    def run_validation(self) -> Optional[Dict[str, Any]]:
        """Runs validation checks against the database."""
        logger.info("Starting dataset validation checks...")

        # Test connection
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as e:
            logger.error(f"Cannot connect to the database defined in .env: {e}")
            logger.info("Validation run aborted: Connection failed.")
            return None

        results: Dict[str, Any] = {
            "duplicate_players": 0,
            "duplicate_teams": 0,
            "duplicate_venues": 0,
            "duplicate_matches": 0,
            "missing_ids": 0,
            "null_values_key_fields": 0,
            "broken_foreign_keys": 0,
            "incorrect_overs_format": 0,
            "details": [],
        }

        with get_db() as session:
            # 1. Check Duplicate Players (duplicates on name/id)
            dup_players = session.execute(
                text(
                    "SELECT name, COUNT(*) FROM players GROUP BY name HAVING COUNT(*) > 1"
                )
            ).fetchall()
            results["duplicate_players"] = len(dup_players)
            for dp in dup_players:
                results["details"].append(
                    {
                        "table": "players",
                        "type": "Duplicate Name",
                        "description": f"Player '{dp[0]}' is registered {dp[1]} times.",
                        "severity": "Warning",
                    }
                )

            # 2. Check Duplicate Teams
            dup_teams = session.execute(
                text(
                    "SELECT name, COUNT(*) FROM teams GROUP BY name HAVING COUNT(*) > 1"
                )
            ).fetchall()
            results["duplicate_teams"] = len(dup_teams)
            for dt in dup_teams:
                results["details"].append(
                    {
                        "table": "teams",
                        "type": "Duplicate Team",
                        "description": f"Team '{dt[0]}' is registered {dt[1]} times.",
                        "severity": "Warning",
                    }
                )

            # 3. Check Duplicate Venues (same name and city)
            dup_venues = session.execute(
                text(
                    "SELECT name, city, COUNT(*) FROM venues GROUP BY name, city HAVING COUNT(*) > 1"
                )
            ).fetchall()
            results["duplicate_venues"] = len(dup_venues)
            for dv in dup_venues:
                results["details"].append(
                    {
                        "table": "venues",
                        "type": "Duplicate Venue",
                        "description": f"Venue '{dv[0]}' in '{dv[1]}' is registered {dv[2]} times.",
                        "severity": "Warning",
                    }
                )

            # 4. Check Missing Primary Keys or IDs (PK checks)
            tables = [
                "series",
                "venues",
                "teams",
                "players",
                "matches",
                "innings",
                "batting_scores",
                "bowling_scores",
            ]
            for table in tables:
                null_pk = session.execute(
                    text(f"SELECT COUNT(*) FROM {table} WHERE id IS NULL")
                ).scalar()
                if null_pk > 0:
                    results["missing_ids"] += null_pk
                    results["details"].append(
                        {
                            "table": table,
                            "type": "Null ID",
                            "description": f"Table '{table}' contains {null_pk} records with NULL primary key ID.",
                            "severity": "Critical",
                        }
                    )

            # 5. Check NULL values in critical fields (e.g. match teams or formats)
            null_matches = session.execute(
                text(
                    "SELECT COUNT(*) FROM matches WHERE team1_id IS NULL OR team2_id IS NULL OR format IS NULL"
                )
            ).scalar()
            if null_matches > 0:
                results["null_values_key_fields"] += null_matches
                results["details"].append(
                    {
                        "table": "matches",
                        "type": "Missing Match Details",
                        "description": f"Table 'matches' has {null_matches} records missing team IDs or match format.",
                        "severity": "High",
                    }
                )

            # 6. Check Broken Foreign Keys
            # Matches referencing missing venues
            broken_venues = session.execute(
                text(
                    "SELECT COUNT(*) FROM matches m WHERE m.venue_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM venues WHERE id = m.venue_id)"
                )
            ).scalar()
            if broken_venues > 0:
                results["broken_foreign_keys"] += broken_venues
                results["details"].append(
                    {
                        "table": "matches",
                        "type": "Orphan Venue FK",
                        "description": f"{broken_venues} matches reference a venue ID that does not exist.",
                        "severity": "Critical",
                    }
                )

            # Batting Scores referencing missing players
            broken_players = session.execute(
                text(
                    "SELECT COUNT(*) FROM batting_scores bs WHERE NOT EXISTS (SELECT 1 FROM players WHERE id = bs.player_id)"
                )
            ).scalar()
            if broken_players > 0:
                results["broken_foreign_keys"] += broken_players
                results["details"].append(
                    {
                        "table": "batting_scores",
                        "type": "Orphan Player FK",
                        "description": f"{broken_players} batting score records reference a player ID that does not exist.",
                        "severity": "Critical",
                    }
                )

            # 7. Check Incorrect Cricket Overs formats (fractional part must be <= 5, i.e., .1, .2, .3, .4, .5, .0)
            # Check Innings over format
            bad_overs_inn = session.execute(
                text(
                    "SELECT id, match_id, innings_num, overs FROM innings WHERE (overs - FLOOR(overs)) > 0.5"
                )
            ).fetchall()
            results["incorrect_overs_format"] += len(bad_overs_inn)
            for bo in bad_overs_inn:
                results["details"].append(
                    {
                        "table": "innings",
                        "type": "Invalid Overs Format",
                        "description": f"Innings ID {bo[0]} has invalid overs value: {bo[3]}.",
                        "severity": "Medium",
                    }
                )

        return results

    def auto_fix_issues(self) -> int:
        """Attempts to automatically repair data format anomalies in the database."""
        logger.info("Initiating auto-fix engine...")
        fixed_count = 0

        try:
            with get_db() as session:
                # Fix 1: Correct invalid over counts (fractional part > 0.5)
                bad_overs = session.execute(
                    text(
                        "SELECT id, overs FROM innings WHERE (overs - FLOOR(overs)) > 0.5"
                    )
                ).fetchall()

                for row in bad_overs:
                    inn_id = row[0]
                    overs = float(row[1])
                    whole = int(overs)
                    frac = round((overs - whole) * 10)

                    if frac >= 6:
                        # 6 balls = 1 full over
                        new_overs = float(whole + 1)
                        session.execute(
                            text(
                                "UPDATE innings SET overs = :new_overs WHERE id = :id"
                            ),
                            {"new_overs": new_overs, "id": inn_id},
                        )
                        fixed_count += 1
                        logger.info(
                            f"Fixed invalid over count for Innings ID {inn_id}: {overs} -> {new_overs}"
                        )

                session.commit()
        except Exception as e:
            logger.error(f"Auto-fix execution failed: {e}")

        logger.info(f"Auto-fix completed. Total records repaired: {fixed_count}")
        return fixed_count

    def generate_reports(self, results: Dict[str, Any]) -> None:
        """Generates the Markdown Validation Report and CSV Report."""
        if not results:
            return

        # 1. Write Markdown Report
        md_file = self.reports_dir / f"validation_report_{self.timestamp}.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write("# Database Validation Report\n\n")
            f.write(
                f"**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            )
            f.write(f"**Database Engine:** PostgreSQL\n\n")

            f.write("## Validation Summary Metrics\n\n")
            f.write("| Diagnostic Check | Error/Warning Count |\n")
            f.write("| --- | --- |\n")
            f.write(f"| Duplicate Players | {results['duplicate_players']} |\n")
            f.write(f"| Duplicate Teams | {results['duplicate_teams']} |\n")
            f.write(f"| Duplicate Venues | {results['duplicate_venues']} |\n")
            f.write(f"| Duplicate Matches | {results['duplicate_matches']} |\n")
            f.write(f"| Missing IDs (NULL PK) | {results['missing_ids']} |\n")
            f.write(
                f"| Missing Key Values (NULL fields) | {results['null_values_key_fields']} |\n"
            )
            f.write(
                f"| Broken Foreign Keys (Orphans) | {results['broken_foreign_keys']} |\n"
            )
            f.write(
                f"| Incorrect Overs Formats | {results['incorrect_overs_format']} |\n\n"
            )

            f.write("## Detailed Issue Log\n\n")
            if not results["details"]:
                f.write("🎉 **All validation checks passed! No issues detected.**\n")
            else:
                f.write("| Table | Issue Type | Description | Severity |\n")
                f.write("| --- | --- | --- | --- |\n")
                for det in results["details"]:
                    f.write(
                        f"| {det['table']} | {det['type']} | {det['description']} | {det['severity']} |\n"
                    )

        logger.info(
            f"Validation Markdown report saved: processed_data/reports/validation_report_{self.timestamp}.md"
        )

        # 2. Write CSV Report
        csv_file = self.reports_dir / f"validation_errors_{self.timestamp}.csv"
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Table", "IssueType", "Description", "Severity"])
            for det in results["details"]:
                writer.writerow(
                    [det["table"], det["type"], det["description"], det["severity"]]
                )

        logger.info(
            f"Validation CSV report saved: processed_data/reports/validation_errors_{self.timestamp}.csv"
        )

        # Print terminal summary statistics
        print("\n=========================================")
        print("DATABASE VALIDATION STATISTICS SUMMARY")
        print("=========================================")
        print(f"Duplicate Players:  {results['duplicate_players']}")
        print(f"Duplicate Teams:    {results['duplicate_teams']}")
        print(f"Duplicate Venues:   {results['duplicate_venues']}")
        print(f"Orphaned Foreign Keys: {results['broken_foreign_keys']}")
        print(f"Invalid Overs Formats: {results['incorrect_overs_format']}")
        print(f"Total Errors Logged: {len(results['details'])}")
        print("=========================================\n")


def main() -> None:
    validator = DatasetValidator()
    results = validator.run_validation()

    if results:
        # Run auto-fixes if anomalies were detected
        if results["incorrect_overs_format"] > 0:
            fixed = validator.auto_fix_issues()
            if fixed > 0:
                # Re-validate to generate an updated post-fix report
                logger.info("Re-running validation checks after auto-fixes...")
                results = validator.run_validation()

        validator.generate_reports(results)
    else:
        print("\nCould not validate dataset: Database connection unavailable.")
        print("Please check DATABASE_URL in your .env file.\n")


if __name__ == "__main__":
    main()
