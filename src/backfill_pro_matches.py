
"""
Historical professional Dota 2 match backfill.

Day 23:
- Fetch historical matches from OpenDota.
- Paginate using less_than_match_id.
- Collect a bounded number of pages.
- Deduplicate matches by match_id.
- Save historical raw records to JSON.

Checkpoint/resume improvements are scheduled for Day 24.
"""

import argparse
import json
import sys
from pathlib import Path

from opendota_client import fetch_json


RECENT_FILE = Path("data/raw/pro_matches.json")
HISTORY_FILE = Path("data/raw/pro_matches_history.json")

DEFAULT_PAGES = 3
MAX_PAGES = 20


def valid_match_id(value):
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value > 0
    )


def load_json_list(path):
    """Load a JSON list from disk, if it exists."""
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            f"Expected a JSON list in {path}"
        )

    return data


def deduplicate_matches(matches):
    """
    Deduplicate by match ID.

    Preserve the first occurrence, which is adequate
    for this initial raw-history collector.
    """
    seen = set()
    unique = []

    for match in matches:
        if not isinstance(match, dict):
            continue

        match_id = match.get("match_id")

        if not valid_match_id(match_id):
            continue

        if match_id in seen:
            continue

        seen.add(match_id)
        unique.append(match)

    return unique


def oldest_match_id(matches):
    ids = [
        match["match_id"]
        for match in matches
        if isinstance(match, dict)
        and valid_match_id(match.get("match_id"))
    ]

    return min(ids) if ids else None


def collect_history(pages):
    if not RECENT_FILE.exists():
        raise FileNotFoundError(
            f"Missing recent match data: {RECENT_FILE}"
        )

    recent = load_json_list(RECENT_FILE)
    history = load_json_list(HISTORY_FILE)

    boundary = oldest_match_id(recent)

    if boundary is None:
        raise ValueError(
            "Recent dataset contains no valid match IDs"
        )

    # Continue from the oldest previously saved
    # historical match, when available.
    history_boundary = oldest_match_id(history)

    if history_boundary is not None:
        boundary = min(boundary, history_boundary)

    print(f"Starting before match ID: {boundary}")
    print(f"Previously saved historical matches: {len(history)}")

    collected = []

    for page_number in range(1, pages + 1):
        print(f"\nFetching historical page {page_number}/{pages}")

        batch = fetch_json(
            "proMatches",
            params={"less_than_match_id": boundary},
        )

        if batch is None:
            raise RuntimeError(
                f"Failed to fetch historical page {page_number}"
            )

        if not isinstance(batch, list):
            raise ValueError(
                "OpenDota returned an unexpected response"
            )

        if not batch:
            print("No additional historical matches found.")
            break

        # Keep only records strictly before the
        # requested match ID boundary.
        valid_batch = [
            match
            for match in batch
            if isinstance(match, dict)
            and valid_match_id(match.get("match_id"))
            and match["match_id"] < boundary
        ]

        if not valid_batch:
            print("No older valid match IDs in this page.")
            break

        collected.extend(valid_batch)

        next_boundary = oldest_match_id(valid_batch)

        if next_boundary is None or next_boundary >= boundary:
            raise RuntimeError(
                "Historical pagination did not advance"
            )

        boundary = next_boundary

        print(f"Received records: {len(valid_batch)}")
        print(f"Next boundary: {boundary}")

    combined = deduplicate_matches(history + collected)

    # Deterministic output, newest first.
    combined.sort(
        key=lambda match: match["match_id"],
        reverse=True,
    )

    HISTORY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with HISTORY_FILE.open("w", encoding="utf-8") as file:
        json.dump(combined, file, indent=2)

    print("\nBackfill summary")
    print(f"Previously saved: {len(history)}")
    print(f"Newly fetched records: {len(collected)}")
    print(f"Unique historical matches: {len(combined)}")
    print(f"Saved to: {HISTORY_FILE}")

    return combined


def main():
    parser = argparse.ArgumentParser(
        description="Backfill historical Dota 2 professional matches"
    )

    parser.add_argument(
        "--pages",
        type=int,
        default=DEFAULT_PAGES,
        help="Number of historical pages to fetch",
    )

    args = parser.parse_args()

    if not 1 <= args.pages <= MAX_PAGES:
        parser.error(
            f"--pages must be between 1 and {MAX_PAGES}"
        )

    try:
        collect_history(args.pages)
    except (
        FileNotFoundError,
        ValueError,
        RuntimeError,
        json.JSONDecodeError,
        OSError,
    ) as error:
        print(f"ERROR: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
