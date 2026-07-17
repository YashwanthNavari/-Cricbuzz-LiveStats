import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger("ValidatorService")

# Pydantic models for validation

class TeamSchema(BaseModel):
    teamId: int
    teamName: str
    teamSName: Optional[str] = None

class VenueSchema(BaseModel):
    id: Optional[int] = None
    name: str
    city: Optional[str] = None
    country: Optional[str] = None

class MatchInfoSchema(BaseModel):
    matchId: int
    matchDescription: Optional[str] = None
    matchFormat: Optional[str] = None
    matchState: Optional[str] = None
    status: Optional[str] = None
    team1: TeamSchema
    team2: TeamSchema
    venueInfo: Optional[VenueSchema] = None
    startDate: Optional[str] = None

class SeriesAdWrapperSchema(BaseModel):
    seriesId: int
    seriesName: str
    matches: List[Dict[str, Any]]  # Matches can be validated downstream

class SeriesMatchSchema(BaseModel):
    seriesAdWrapper: Optional[SeriesAdWrapperSchema] = None

class TypeMatchSchema(BaseModel):
    matchType: Optional[str] = None
    seriesMatches: List[Dict[str, Any]] = []

class MatchesResponseSchema(BaseModel):
    typeMatches: Optional[List[TypeMatchSchema]] = None

# Scorecard validation schemas
class BatsmanScoreSchema(BaseModel):
    id: int
    runs: Optional[int] = 0
    balls: Optional[int] = 0
    fours: Optional[int] = 0
    sixes: Optional[int] = 0
    strkrate: Optional[Any] = "0.0"
    outdec: Optional[str] = None

class BowlerScoreSchema(BaseModel):
    id: int
    overs: Optional[Any] = "0.0"
    maidens: Optional[int] = 0
    runs: Optional[int] = 0
    wickets: Optional[int] = 0
    economy: Optional[Any] = "0.0"

class InningSchema(BaseModel):
    inningsid: int
    score: Optional[int] = 0
    wickets: Optional[int] = 0
    overs: Optional[float] = 0.0
    batsman: Optional[List[BatsmanScoreSchema]] = []
    bowler: Optional[List[BowlerScoreSchema]] = []

class ScorecardResponseSchema(BaseModel):
    scorecard: List[InningSchema]


# Player validation schemas
class PlayerResponseSchema(BaseModel):
    id: int
    name: str
    battingStyle: Optional[str] = None
    bowlingStyle: Optional[str] = None
    role: Optional[str] = None
    image: Optional[str] = None


def validate_matches_json(data: Dict[str, Any]) -> bool:
    """Validates the matches list JSON structure."""
    try:
        if "typeMatches" not in data and "matches" not in data:
            logger.error("JSON lacks 'typeMatches' or 'matches' key")
            return False
        # If typeMatches is present, validate structure
        if "typeMatches" in data:
            MatchesResponseSchema(**data)
        return True
    except ValidationError as e:
        logger.error(f"Matches JSON validation failed: {e}")
        return False

def validate_scorecard_json(data: Dict[str, Any]) -> bool:
    """Validates the scorecard JSON structure."""
    try:
        if "scorecard" not in data:
            logger.error("JSON lacks 'scorecard' key")
            return False
        ScorecardResponseSchema(**data)
        return True
    except ValidationError as e:
        logger.error(f"Scorecard JSON validation failed: {e}")
        return False

def validate_player_json(data: Dict[str, Any]) -> bool:
    """Validates the player details JSON structure."""
    try:
        # Cricbuzz API player endpoint can return wrapper
        player_data = data.get("player", data)
        if "id" not in player_data and "playerId" in player_data:
            player_data["id"] = player_data["playerId"]
        
        PlayerResponseSchema(**player_data)
        return True
    except ValidationError as e:
        logger.error(f"Player JSON validation failed: {e}")
        return False
