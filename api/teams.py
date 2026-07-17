from typing import Any, Dict
from .client import CricbuzzClient


def get_team_results(client: CricbuzzClient, team_id: int) -> Dict[str, Any]:
    """
    Fetches past results for a specific team.
    """
    endpoint = f"teams/v1/{team_id}/results"
    return client.request(endpoint, method="GET")


def get_team_schedule(client: CricbuzzClient, team_id: int) -> Dict[str, Any]:
    """
    Fetches the upcoming match schedule for a specific team.
    """
    endpoint = f"teams/v1/{team_id}/schedule"
    return client.request(endpoint, method="GET")
