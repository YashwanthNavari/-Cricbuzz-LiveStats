import logging
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
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

logger = logging.getLogger("TransformerService")


def parse_date(date_val: Any) -> Optional[datetime]:
    """Helper to parse datetime from timestamp (ms) or string."""
    if not date_val:
        return None
    try:
        if isinstance(date_val, (int, float)):
            return datetime.fromtimestamp(date_val / 1000.0, tz=timezone.utc)
        if isinstance(date_val, str):
            if date_val.isdigit():
                return datetime.fromtimestamp(int(date_val) / 1000.0, tz=timezone.utc)
            # Try parsing ISO or standard date formats
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
                try:
                    return datetime.strptime(date_val, fmt)
                except ValueError:
                    continue
    except Exception as e:
        logger.warning(f"Failed to parse date '{date_val}': {e}")
    return None


def parse_dismissal_type(out_desc: Optional[str]) -> Optional[str]:
    """Helper to categorize the dismissal type from standard cricket commentary descriptions."""
    if not out_desc:
        return None
    desc = out_desc.lower().strip()
    if not desc or "not out" in desc or "retired" in desc:
        return "not out"
    if desc.startswith("c ") and " b " in desc:
        return "caught"
    if desc.startswith("lbw b"):
        return "lbw"
    if desc.startswith("b "):
        return "bowled"
    if desc.startswith("st ") and " b " in desc:
        return "stumped"
    if "run out" in desc:
        return "run out"
    if "hit wicket" in desc:
        return "hit wicket"
    return "other"


def transform_series(data: Dict[str, Any]) -> Series:
    """Transforms raw series dictionary into Series ORM model."""
    start_dt = parse_date(data.get("startDate"))
    end_dt = parse_date(data.get("endDate"))
    return Series(
        id=int(data["seriesId"]),
        name=data["seriesName"],
        start_date=start_dt.date() if start_dt else None,
        end_date=end_dt.date() if end_dt else None,
        series_type=data.get("seriesType"),
    )


def transform_venue(data: Dict[str, Any]) -> Venue:
    """Transforms raw venue dictionary into Venue ORM model."""
    return Venue(
        id=int(data["id"]) if data.get("id") is not None else None,
        name=data.get("ground") or data.get("name") or "Unknown Venue",
        city=data.get("city"),
        country=data.get("country"),
        capacity=data.get("capacity"),
    )


def transform_team(data: Dict[str, Any]) -> Team:
    """Transforms raw team dictionary into Team ORM model."""
    return Team(
        id=int(data["teamId"]), name=data["teamName"], short_name=data.get("teamSName")
    )


def transform_player(data: Dict[str, Any]) -> Player:
    """Transforms raw player dictionary into Player ORM model."""
    player_data = data.get("player", data)
    return Player(
        id=int(player_data.get("id") or player_data.get("playerId")),
        name=player_data["name"],
        role=player_data.get("role"),
        batting_style=player_data.get("battingStyle"),
        bowling_style=player_data.get("bowlingStyle"),
        image_url=player_data.get("image") or player_data.get("imageUrl"),
    )


def transform_match(data: Dict[str, Any], series_id: Optional[int] = None) -> Match:
    """Transforms raw match dictionary into Match ORM model."""
    match_info = data.get("matchInfo", data)

    venue_info = match_info.get("venueInfo")
    venue_id = None
    if venue_info and venue_info.get("id"):
        venue_id = int(venue_info["id"])

    start_time = parse_date(
        match_info.get("startDate") or match_info.get("matchStartTimestamp")
    )

    # Extract toss details
    toss_winner_id = None
    toss_decision = None
    toss_results = match_info.get("tossResults")
    if toss_results:
        toss_winner_id = toss_results.get("tossWinnerId")
        toss_decision = toss_results.get("decision")

    winner_id = None
    result = match_info.get("result")
    if result:
        winner_id = result.get("winnerId")

    match_format = (match_info.get("matchFormat") or "").lower().strip()
    overs_limit = 20
    if "odi" in match_format:
        overs_limit = 50
    elif "test" in match_format:
        overs_limit = 90
    elif "t20" in match_format:
        overs_limit = 20

    return Match(
        id=int(match_info["matchId"]),
        series_id=series_id or match_info.get("seriesId"),
        venue_id=venue_id,
        match_desc=match_info.get("matchDescription") or match_info.get("matchDesc"),
        format=match_info.get("matchFormat"),
        status=match_info.get("status"),
        team1_id=int(match_info["team1"]["teamId"]),
        team2_id=int(match_info["team2"]["teamId"]),
        toss_winner_id=int(toss_winner_id) if toss_winner_id else None,
        toss_decision=toss_decision,
        winner_id=int(winner_id) if winner_id else None,
        match_start_time=start_time,
        match_overs_limit=overs_limit,
    )


def transform_scorecard(
    data: Dict[str, Any],
    match_id: int,
    team1_id: int,
    team2_id: int,
    team_name_to_id: Dict[str, int],
) -> List[Innings]:
    """
    Transforms raw scorecard dictionary into a list of Innings ORM models,
    including their nested BattingScore, BowlingScore, and Partnership children.
    """
    innings_list = []
    match_players = extract_players_from_scorecard(data)

    raw_scorecards = data.get("scorecard", [])
    for raw_inn in raw_scorecards:
        innings_num = int(raw_inn["inningsid"])

        # Resolve batting and bowling teams
        bat_team_name = (raw_inn.get("batteamname") or "").lower().strip()
        batting_team_id = team_name_to_id.get(bat_team_name)
        if not batting_team_id:
            # Try to match key team name parts
            matched = False
            for k_name, t_id in team_name_to_id.items():
                if k_name in bat_team_name or bat_team_name in k_name:
                    batting_team_id = t_id
                    matched = True
                    break
            if not matched:
                batting_team_id = team1_id if innings_num == 1 else team2_id

        bowling_team_id = team2_id if batting_team_id == team1_id else team1_id

        # Extract extras
        extras_data = raw_inn.get("extras", {})
        extras_val = int(extras_data.get("total", 0))
        wides_val = int(extras_data.get("wides", 0))
        no_balls_val = int(extras_data.get("noballs", 0))
        byes_val = int(extras_data.get("byes", 0))
        leg_byes_val = int(extras_data.get("legbyes", 0))

        inning = Innings(
            match_id=match_id,
            innings_num=innings_num,
            batting_team_id=batting_team_id,
            bowling_team_id=bowling_team_id,
            runs=int(raw_inn.get("score", 0)),
            wickets=int(raw_inn.get("wickets", 0)),
            overs=float(raw_inn.get("overs", 0.0)),
            extras=extras_val,
            wides=wides_val,
            no_balls=no_balls_val,
            byes=byes_val,
            leg_byes=leg_byes_val,
        )

        # Add batsman scores
        batsmen_list = raw_inn.get("batsman", [])
        for raw_bat in batsmen_list:
            player_id = int(raw_bat["id"])
            runs = int(raw_bat.get("runs", 0))
            balls = int(raw_bat.get("balls", 0))
            out_desc = raw_bat.get("outdec")

            if balls == 0 and runs == 0 and not out_desc:
                continue  # Did not bat

            dismissal_type = parse_dismissal_type(out_desc)
            sr_str = raw_bat.get("strkrate") or "0.0"
            try:
                strike_rate = float(sr_str)
            except ValueError:
                strike_rate = 0.0

            # Entity resolution for bowler and fielder IDs from text description
            bowler_id = None
            fielder_id = None
            if out_desc:
                desc = out_desc.lower().strip()
                if " b " in desc:
                    parts = desc.split(" b ")
                    bowler_part = parts[-1].strip()
                    for p in match_players:
                        if p.name.lower() in bowler_part:
                            bowler_id = p.id
                            break
                if desc.startswith("c ") or desc.startswith("st "):
                    fielder_part = desc.split(" b ")[0].strip()
                    if fielder_part.startswith("c "):
                        fielder_part = fielder_part[2:].strip()
                    elif fielder_part.startswith("st "):
                        fielder_part = fielder_part[3:].strip()
                    for p in match_players:
                        if (
                            p.name.lower() in fielder_part
                            or fielder_part in p.name.lower()
                        ):
                            if p.id != bowler_id:
                                fielder_id = p.id
                                break

            bat_score = BattingScore(
                player_id=player_id,
                runs=runs,
                balls=balls,
                fours=int(raw_bat.get("fours", 0)),
                sixes=int(raw_bat.get("sixes", 0)),
                strike_rate=strike_rate,
                out="not out" not in str(out_desc).lower(),
                dismissal_type=dismissal_type,
                dismissal_text=out_desc,
                bowler_id=bowler_id,
                fielder_id=fielder_id,
            )
            inning.batting_scores.append(bat_score)

        # Add bowler scores
        bowlers_list = raw_inn.get("bowler", [])
        for raw_bowl in bowlers_list:
            player_id = int(raw_bowl["id"])
            ov_str = raw_bowl.get("overs") or "0.0"
            try:
                overs = float(ov_str)
            except ValueError:
                overs = 0.0

            econ_str = raw_bowl.get("economy") or "0.0"
            try:
                economy = float(econ_str)
            except ValueError:
                economy = 0.0

            bowl_score = BowlingScore(
                player_id=player_id,
                overs=overs,
                maidens=int(raw_bowl.get("maidens", 0)),
                runs_conceded=int(raw_bowl.get("runs", 0)),
                wickets=int(raw_bowl.get("wickets", 0)),
                economy=economy,
            )
            inning.bowling_scores.append(bowl_score)

        # Add partnerships
        part_data = raw_inn.get("partnership", {})
        if isinstance(part_data, dict):
            part_list = part_data.get("partnership", [])
            for raw_part in part_list:
                batsman1_id = int(raw_part["bat1id"])
                batsman2_id = int(raw_part["bat2id"])
                p_runs = int(raw_part.get("totalruns", 0))
                p_balls = int(raw_part.get("totalballs", 0))
                fours = int(raw_part.get("bat1fours", 0)) + int(
                    raw_part.get("bat2fours", 0)
                )
                sixes = int(raw_part.get("bat1sixes", 0)) + int(
                    raw_part.get("bat2sixes", 0)
                )

                part = Partnership(
                    batsman1_id=batsman1_id,
                    batsman2_id=batsman2_id,
                    runs=p_runs,
                    balls=p_balls,
                    boundaries_fours=fours,
                    boundaries_sixes=sixes,
                    unbroken=False,
                )
                inning.partnerships.append(part)

        innings_list.append(inning)

    return innings_list


def extract_players_from_scorecard(data: Dict[str, Any]) -> List[Player]:
    """Extracts unique Player model instances from scorecard data."""
    players_dict = {}
    raw_scorecards = data.get("scorecard", [])
    for raw_inn in raw_scorecards:
        # Parse batsmen
        batsmen_list = raw_inn.get("batsman", [])
        for raw_bat in batsmen_list:
            player_id = int(raw_bat["id"])
            name = (
                raw_bat.get("name") or raw_bat.get("nickname") or f"Player {player_id}"
            )
            players_dict[player_id] = Player(id=player_id, name=name)

        # Parse bowlers
        bowlers_list = raw_inn.get("bowler", [])
        for raw_bowl in bowlers_list:
            player_id = int(raw_bowl["id"])
            name = (
                raw_bowl.get("name")
                or raw_bowl.get("nickname")
                or f"Player {player_id}"
            )
            players_dict[player_id] = Player(id=player_id, name=name)

    return list(players_dict.values())
