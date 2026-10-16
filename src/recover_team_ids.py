import json
import random
import time
from collections import Counter
from pathlib import Path
from opendota_client import fetch_json
import requests


# ==========================================
# 1. CONFIGURATION
# ==========================================

MATCH_ID = 9040915797

HISTORY_LIMIT = 20
MAX_CANDIDATES_PER_TEAM = 15

REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
REQUEST_DELAY = 1.5

CACHE_DIR = Path("data/cache/opendota")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

SESSION = requests.Session()


# ==========================================
# 2. API CLIENT WITH CACHING AND RETRIES
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

    if cache_path.exists():
        try:
            with cache_path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            print(f"[CACHE] {endpoint}")
            return data

        except (json.JSONDecodeError, OSError):
            print(f"[CACHE INVALID] {endpoint}")

    url = f"https://api.opendota.com/api/{endpoint.lstrip('/')}"

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
                time.sleep((2 ** attempt) + random.uniform(0, 1))

    print(f"[SKIPPED] {endpoint}")
    return None


# ==========================================
# 3. EXTRACT PLAYER ROSTERS
# ==========================================

def get_match_rosters(match):
    radiant_players = set()
    dire_players = set()

    for player in match.get("players", []):
        account_id = player.get("account_id")
        player_slot = player.get("player_slot")

        if account_id is None or player_slot is None:
            continue

        if player_slot < 128:
            radiant_players.add(account_id)
        else:
            dire_players.add(account_id)

    return radiant_players, dire_players


# ==========================================
# 4. DISCOVER AND RANK HISTORICAL MATCHES
# ==========================================

def discover_candidates(roster, before_timestamp):
    match_counts = Counter()

    for account_id in sorted(roster):
        history = fetch_json(
            f"players/{account_id}/matches",
            params={"limit": HISTORY_LIMIT},
        )

        if history is None:
            print(f"Player {account_id}: unavailable")
            continue

        historical_ids = {
            item["match_id"]
            for item in history
            if item.get("match_id") is not None
            and item.get("start_time") is not None
            and item["start_time"] < before_timestamp
        }

        print(
            f"Player {account_id}: "
            f"{len(historical_ids)} earlier matches"
        )

        match_counts.update(historical_ids)

    # Prioritize matches shared by more players
    return sorted(
        match_counts.items(),
        key=lambda item: (-item[1], -item[0]),
    )


# ==========================================
# 5. RECOVER TEAM ID
# ==========================================

def recover_team_id(side, target_roster, before_timestamp):
    if len(target_roster) != 5:
        print(f"{side}: incomplete target roster")
        return None

    candidates = discover_candidates(
        target_roster,
        before_timestamp,
    )

    print(f"{side}: {len(candidates)} candidate matches discovered")

    for reference_id, history_count in candidates[:MAX_CANDIDATES_PER_TEAM]:
        reference = fetch_json(f"matches/{reference_id}")

        if reference is None:
            continue

        reference_time = reference.get("start_time")

        if reference_time is None or reference_time >= before_timestamp:
            continue

        ref_radiant, ref_dire = get_match_rosters(reference)

        reference_teams = [
            (
                ref_radiant,
                reference.get("radiant_team_id"),
                reference.get("radiant_name"),
            ),
            (
                ref_dire,
                reference.get("dire_team_id"),
                reference.get("dire_name"),
            ),
        ]

        for roster, team_id, team_name in reference_teams:
            if (
                len(roster) == 5
                and roster == target_roster
                and team_id is not None
            ):
                result = {
                    "side": side,
                    "team_id_candidate": team_id,
                    "team_name_candidate": team_name,
                    "reference_match_id": reference_id,
                    "matched_players": 5,
                    "history_count": history_count,
                }

                return result

    return None


# ==========================================
# 6. MAIN
# ==========================================

def main():
    match = fetch_json(f"matches/{MATCH_ID}")

    if match is None:
        print("Target match unavailable.")
        return

    target_timestamp = match.get("start_time")

    if target_timestamp is None:
        print("Target match missing timestamp.")
        return

    radiant, dire = get_match_rosters(match)

    print(f"\nMatch: {MATCH_ID}")
    print(f"Radiant roster: {sorted(radiant)}")
    print(f"Dire roster: {sorted(dire)}")

    print("\n===== AUTOMATIC TEAM ID RECOVERY =====")

    for side, roster in [
        ("Radiant", radiant),
        ("Dire", dire),
    ]:
        print(f"\n--- {side} ---")

        result = recover_team_id(
            side,
            roster,
            target_timestamp,
        )

        if result:
            print(
                f"\nRECOVERED {side}: "
                f"{result['team_name_candidate']} "
                f"(Team ID: {result['team_id_candidate']})"
            )
            print(
                f"Evidence match: {result['reference_match_id']}"
            )
            print(
                f"Matching players: {result['matched_players']}/5"
            )
            print(
                f"Players whose histories contained the match: "
                f"{result['history_count']}/5"
            )
        else:
            print(f"No verified candidate found for {side}.")

    print("\n===== RECOVERY COMPLETE =====")


if __name__ == "__main__":
    main()