from typing import Any, Dict
from .client import CricbuzzClient

def get_series_list(client: CricbuzzClient) -> Dict[str, Any]:
    """
    Fetches the list of active/recent/upcoming cricket series.
    """
    endpoint = "series/v1/list"
    return client.request(endpoint, method="GET")

def get_series_matches(client: CricbuzzClient, series_id: int) -> Dict[str, Any]:
    """
    Fetches all matches associated with a specific series.
    """
    endpoint = f"series/v1/{series_id}"
    return client.request(endpoint, method="GET")
