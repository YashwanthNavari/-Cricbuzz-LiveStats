from typing import Any, Dict
from .client import CricbuzzClient

def get_venue_matches(client: CricbuzzClient, venue_id: int) -> Dict[str, Any]:
    """
    Fetches the matches scheduled at a specific venue ID.
    """
    endpoint = f"venues/v1/{venue_id}"
    return client.request(endpoint, method="GET")
