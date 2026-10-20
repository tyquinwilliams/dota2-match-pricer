
"""
Reusable OpenDota API client.

Features:
- Local JSON response caching
- Request throttling
- Request timeouts
- Retries for temporary failures
- HTTP 429 Retry-After handling
- Exponential backoff with jitter
- Structured failure logging
"""

import json
import os
import random
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import requests


BASE_URL = "https://api.opendota.com/api"

CACHE_DIR = Path("data/cache/opendota")
LOG_DIR = Path("data/logs")
ERROR_LOG = LOG_DIR / "opendota_errors.jsonl"

REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
REQUEST_DELAY = 1.5
MAX_RETRY_DELAY = 60

SESSION = requests.Session()

# Tracks the most recent real API request.
# Cache hits do not require throttling.
LAST_REQUEST_TIME = 0.0


def log_failure(endpoint, params, attempt, error, status_code=None):
    """Append a structured API failure event to a JSONL file."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    event = {
        "timestamp_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "endpoint": endpoint,
        "params": params,
        "attempt": attempt,
        "status_code": status_code,
        "error": str(error),
    }

    with ERROR_LOG.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event) + "\n")


def throttle_request():
    """Ensure a minimum delay between real API requests."""
    global LAST_REQUEST_TIME

    elapsed = time.monotonic() - LAST_REQUEST_TIME

    if LAST_REQUEST_TIME > 0 and elapsed < REQUEST_DELAY:
        time.sleep(REQUEST_DELAY - elapsed)

    LAST_REQUEST_TIME = time.monotonic()


def retry_after_seconds(response):
    """
    Read Retry-After as either a number of seconds
    or an HTTP date.
    """
    header = response.headers.get("Retry-After")

    if not header:
        return None

    try:
        return max(0.0, float(header))
    except ValueError:
        pass

    try:
        retry_date = parsedate_to_datetime(header)

        if retry_date.tzinfo is None:
            retry_date = retry_date.replace(
                tzinfo=timezone.utc
            )

        delay = (
            retry_date - datetime.now(timezone.utc)
        ).total_seconds()

        return max(0.0, delay)

    except (TypeError, ValueError, OverflowError):
        return None


def backoff_seconds(attempt, response=None):
    """Calculate bounded exponential backoff."""
    delay = (2 ** attempt) + random.uniform(0, 1)

    if response is not None and response.status_code == 429:
        retry_after = retry_after_seconds(response)

        if retry_after is not None:
            delay = max(delay, retry_after)

    return min(delay, MAX_RETRY_DELAY)


def cache_path_for(endpoint, params):
    cache_name = endpoint.strip("/").replace("/", "_")

    if params:
        suffix = "_".join(
            f"{key}_{value}"
            for key, value in sorted(params.items())
        )
        cache_name += f"_{suffix}"

    return CACHE_DIR / f"{cache_name}.json"


def fetch_json(endpoint, params=None):
    """Fetch JSON from OpenDota, with caching and retries."""
    params = params or {}
    cache_path = cache_path_for(endpoint, params)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if cache_path.exists():
        try:
            with cache_path.open(
                "r", encoding="utf-8"
            ) as file:
                data = json.load(file)

            print(f"[CACHE] {endpoint}")
            return data

        except (json.JSONDecodeError, OSError):
            print(f"[CACHE INVALID] {endpoint}")

    url = f"{BASE_URL}/{endpoint.lstrip('/')}"

    retryable_statuses = {429, 500, 502, 503, 504}

    for attempt in range(1, MAX_RETRIES + 1):
        throttle_request()
        response = None

        try:
            response = SESSION.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )

            response.raise_for_status()
            data = response.json()

            temporary_path = cache_path.with_name(
                cache_path.name + ".tmp"
            )

            try:
                with temporary_path.open(
                    "w", encoding="utf-8"
                ) as file:
                    json.dump(data, file)
                    file.flush()
                    os.fsync(file.fileno())

                os.replace(temporary_path, cache_path)

            finally:
                if temporary_path.exists():
                    temporary_path.unlink()

            print(f"[API OK] {endpoint}")
            return data

        except requests.exceptions.HTTPError as error:
            status_code = (
                response.status_code
                if response is not None
                else None
            )

            log_failure(
                endpoint,
                params,
                attempt,
                error,
                status_code,
            )

            print(
                f"[HTTP ERROR] {endpoint} "
                f"status={status_code} "
                f"attempt={attempt}/{MAX_RETRIES}"
            )

            if status_code not in retryable_statuses:
                break

            if attempt < MAX_RETRIES:
                delay = backoff_seconds(attempt, response)
                print(f"[RETRY] Waiting {delay:.1f}s")
                time.sleep(delay)

        except (
            requests.exceptions.RequestException,
            ValueError,
        ) as error:
            log_failure(
                endpoint,
                params,
                attempt,
                error,
            )

            print(
                f"[API ERROR] {endpoint} "
                f"attempt={attempt}/{MAX_RETRIES}: {error}"
            )

            if attempt < MAX_RETRIES:
                delay = backoff_seconds(attempt)
                print(f"[RETRY] Waiting {delay:.1f}s")
                time.sleep(delay)

    print(f"[SKIPPED] {endpoint}")
    return None


def get_match(match_id):
    """Retrieve a Dota 2 match by ID."""
    return fetch_json(f"matches/{match_id}")
