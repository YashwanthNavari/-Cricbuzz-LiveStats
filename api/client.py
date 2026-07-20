import os
import time
import logging
import uuid
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import requests
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("CricbuzzClient")


class CricbuzzClient:
    """
    Base client for making authenticated requests to the Cricbuzz Cricket API on RapidAPI.
    Handles configuration, retries, timeouts, rate limiting, logging, and raw response persistence.
    """

    def __init__(self) -> None:
        load_dotenv()
        self.api_key: Optional[str] = os.getenv("RAPIDAPI_KEY")
        self.api_host: str = os.getenv(
            "RAPIDAPI_HOST", "cricbuzz-cricket.p.rapidapi.com"
        )

        if not self.api_key or self.api_key == "your_rapidapi_key_here":
            try:
                import streamlit as st

                self.api_key = st.secrets.get("RAPIDAPI_KEY") or self.api_key
                self.api_host = st.secrets.get("RAPIDAPI_HOST") or self.api_host
            except Exception:
                pass

        self.base_url: str = f"https://{self.api_host}"

        if not self.api_key or self.api_key == "your_rapidapi_key_here":
            logger.warning(
                "RAPIDAPI_KEY is not configured or is set to placeholder in .env"
            )

        self.session = requests.Session()
        self.session.headers.update(
            {
                "x-rapidapi-key": self.api_key or "",
                "x-rapidapi-host": self.api_host,
                "Content-Type": "application/json",
            }
        )

        # Setup raw_data directory path
        current_file = Path(__file__).resolve()
        # Workspace root is one level up from api/client.py in the new flat structure
        self.workspace_root: Path = current_file.parents[1]
        self.raw_data_dir: Path = self.workspace_root / "raw_data"
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)

        # Also ensure logs directory exists
        self.logs_dir: Path = self.workspace_root / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        timeout: int = 15,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
    ) -> Dict[str, Any]:
        """
        Sends an HTTP request to the Cricbuzz API, handles rate limits and retries,
        persists the raw response in raw_data, and returns the response JSON.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        endpoint_clean = endpoint.strip("/").replace("/", "_")

        last_status_code = None
        last_error_message = ""

        for attempt in range(max_retries + 1):
            logger.info(
                f"Sending {method} {url} | Params: {params} | Attempt: {attempt + 1}"
            )
            start_time = time.time()

            try:
                response = self.session.request(
                    method=method, url=url, params=params, json=data, timeout=timeout
                )
                latency = time.time() - start_time
                last_status_code = response.status_code
                logger.info(
                    f"Response status: {response.status_code} | Latency: {latency:.2f}s"
                )

                # Handle HTTP 429 (Too Many Requests / Rate Limit / Quota Exceeded)
                if response.status_code == 429:
                    try:
                        error_json = response.json()
                        last_error_message = error_json.get("message", "")
                    except Exception:
                        last_error_message = response.text or ""

                    # Detect if we hit a hard quota limit (e.g. daily/monthly limit reached).
                    # If so, abort immediately since retrying won't help.
                    quota_terms = ["quota", "limit exceeded", "subscribe to a subscription plan", "monthly limit", "daily limit"]
                    if any(term in last_error_message.lower() for term in quota_terms):
                        raise Exception(f"RapidAPI Quota Exceeded: {last_error_message}")

                    retry_after = response.headers.get("Retry-After")
                    sleep_time = (
                        int(retry_after)
                        if (retry_after and retry_after.isdigit())
                        else (backoff_factor**attempt)
                    )
                    logger.warning(
                        f"Rate limited (429). Retrying after sleeping for {sleep_time}s... Message: {last_error_message}"
                    )
                    time.sleep(sleep_time)
                    continue

                # Handle transient 5xx server errors
                if response.status_code >= 500 and attempt < max_retries:
                    sleep_time = backoff_factor**attempt
                    logger.warning(
                        f"Server error ({response.status_code}). Retrying in {sleep_time}s..."
                    )
                    time.sleep(sleep_time)
                    continue

                # Raise HTTP exceptions for any bad status
                response.raise_for_status()

                # Parse JSON
                try:
                    response_json = response.json()
                except ValueError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    raise ValueError(
                        f"Invalid JSON returned from server: {response.text}"
                    ) from e

                # Save raw response to files to maintain complete API raw logs
                self._save_raw_response(endpoint_clean, response_json)

                return response_json

            except requests.exceptions.Timeout as e:
                logger.error(f"Timeout on attempt {attempt + 1} for {url}: {e}")
                if attempt < max_retries:
                    sleep_time = backoff_factor**attempt
                    logger.info(f"Retrying in {sleep_time}s...")
                    time.sleep(sleep_time)
                else:
                    raise
            except requests.exceptions.RequestException as e:
                logger.error(f"HTTP request error: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    response_text = ""
                    try:
                        response_text = e.response.text
                        err_json = e.response.json()
                        msg = err_json.get("message", "")
                        if msg:
                            raise Exception(f"API Error ({e.response.status_code}): {msg}") from e
                    except Exception:
                        if response_text:
                            # Truncate response text if it is long HTML
                            truncated_text = response_text[:200] + "..." if len(response_text) > 200 else response_text
                            raise Exception(f"API Error ({e.response.status_code}): {truncated_text}") from e
                raise

        err_detail = f"Status {last_status_code}"
        if last_error_message:
            err_detail += f" - {last_error_message}"
        raise Exception(f"Max retries ({max_retries}) reached for endpoint: {endpoint} ({err_detail})")

    def _save_raw_response(self, entity_name: str, data: Dict[str, Any]) -> None:
        """Saves the raw JSON response to a structured subfolder inside raw_data/ ensuring no overwrite."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        uid = uuid.uuid4().hex[:6]

        entity_dir = self.raw_data_dir / entity_name
        entity_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{entity_name}_{timestamp}_{uid}.json"
        filepath = entity_dir / filename

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved raw response to: raw_data/{entity_name}/{filename}")
        except Exception as e:
            logger.error(f"Failed to save raw response to file {filepath}: {e}")
