from typing import Any, Dict
from .client import CricbuzzClient

def get_match_scorecard(client: CricbuzzClient, match_id: int) -> Dict[str, Any]:
    """
    Fetches the full scorecard (hscard) for a specific match ID.
    """
    endpoint = f"mcenter/v1/{match_id}/hscard"
    return client.request(endpoint, method="GET")
