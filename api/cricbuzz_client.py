"""Small client for the Cricbuzz Cricket API (RapidAPI) with retries and clear errors."""
import logging
import time
from typing import Optional

import requests

import config

logger = logging.getLogger(__name__)


class ApiError(Exception):
    """Raised when the API cannot return usable data (message is safe to show users)."""


class CricbuzzClient:
    """Wraps requests.Session: adds auth headers, retries, and error translation."""

    def __init__(self, api_key: Optional[str] = None, host: Optional[str] = None,
                 timeout: int = config.REQUEST_TIMEOUT, max_retries: int = config.MAX_RETRIES) -> None:
        self.api_key = api_key or config.RAPIDAPI_KEY
        self.host = host or config.RAPIDAPI_HOST
        self.timeout = timeout
        self.max_retries = max_retries
        if not self.api_key:
            raise ApiError("RAPIDAPI_KEY is missing. Add it to your .env file.")
        self.session = requests.Session()
        self.session.headers.update({"x-rapidapi-key": self.api_key,
                                     "x-rapidapi-host": self.host})

    def get(self, path: str, params: Optional[dict] = None) -> dict:
        """GET https://<host><path> and return the parsed JSON.

        Retries on network errors, HTTP 429 and 5xx. Never includes the key in errors.
        """
        url = f"https://{self.host}{path}"
        last_error = "unknown error"
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
            except requests.exceptions.RequestException as exc:
                last_error = f"network problem ({type(exc).__name__})"
            else:
                code = response.status_code
                if code == 200:
                    try:
                        return response.json()
                    except ValueError as exc:
                        raise ApiError("The API returned invalid JSON.") from exc
                if code in (401, 403):
                    raise ApiError(f"API key rejected or plan not subscribed (HTTP {code}).")
                if code == 404:
                    raise ApiError(f"Endpoint not found: {path}")
                if code == 429 or code >= 500:
                    last_error = f"HTTP {code} (rate limit or server issue)"
                else:
                    raise ApiError(f"Unexpected response (HTTP {code}).")
            logger.warning("API attempt %s/%s failed: %s", attempt, self.max_retries, last_error)
            if attempt < self.max_retries:
                time.sleep(2 ** (attempt - 1))  # 1s, 2s, ...
        raise ApiError(f"API failed after {self.max_retries} attempts: {last_error}")
