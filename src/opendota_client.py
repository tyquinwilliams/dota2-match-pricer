import json
import random
import time
from pathlib import Path

import requests


# ==========================================
# CONFIGURATION
# ==========================================

BASE_URL = "https://api.opendota.com/api"

CACHE_DIR = Path("data/cache/opendota")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
REQUEST_DELAY = 1.5

SESSION = requests.Session()


# ==========================================
# REUSABLE API REQUEST FUNCTION
# ==========================================

def fetch_json(endpoint, params=None):
    params = params or {}

    cache_name = endpoint.strip("/").replace("/", "_")

    if params:
        suffix = "_".join(
            f"{key}_{value}"
            for key, value in sorted(params.items())
        )
        cache_name += f"_{suffix}"

    cache_path = CACHE_DIR / f"{cache_name}.json"

    # Read existing cache
    if cache_path.exists():
        try:
            with cache_path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            print(f"[CACHE] {endpoint}")
            return data

        except (json.JSONDecodeError, OSError):
            print(f"[CACHE INVALID] {endpoint}")

    url = f"{BASE_URL}/{endpoint.lstrip('/')}"

    for attempt in range(1, MAX_RETRIES + 1):
        time.sleep(REQUEST_DELAY)

        try:
            response = SESSION.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )

            response.raise_for_status()
            data = response.json()

            with cache_path.open("w", encoding="utf-8") as file:
                json.dump(data, file)

            print(f"[API OK] {endpoint}")
            return data

        except (requests.exceptions.RequestException, ValueError) as error:
            print(
                f"[API ERROR] {endpoint} "
                f"attempt {attempt}/{MAX_RETRIES}: {error}"
            )

            if attempt < MAX_RETRIES:
                backoff = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(backoff)

    print(f"[SKIPPED] {endpoint}")
    return None


# ==========================================
# REUSABLE MATCH RETRIEVAL
# ==========================================

def get_match(match_id):
    """
    Retrieve a Dota 2 match by ID.

    Uses local caching and retries failed requests.
    Returns match data as a dictionary, or None.
    """

    return fetch_json(f"matches/{match_id}")