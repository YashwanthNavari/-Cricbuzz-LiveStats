from typing import Any, Dict
from .client import CricbuzzClient


def get_player_info(client: CricbuzzClient, player_id: int) -> Dict[str, Any]:
    """
    Fetches the profile and metadata of a player by player ID.
    """
    endpoint = f"stats/v1/player/{player_id}"
    return client.request(endpoint, method="GET")
