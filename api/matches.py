from typing import Any, Dict, Optional
from .client import CricbuzzClient


def get_matches_list(
    client: CricbuzzClient,
    match_type: str = "recent",
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Fetches the matches list.
    match_type must be one of: 'live', 'recent', or 'upcoming'.
    """
    if match_type not in ("live", "recent", "upcoming"):
        raise ValueError("match_type must be one of 'live', 'recent', or 'upcoming'")

    endpoint = f"matches/v1/{match_type}"
    return client.request(endpoint, method="GET", params=params)
