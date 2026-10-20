
"""
Historical professional Dota 2 match backfill.

Day 24:
- Fetch older professional matches from OpenDota.
- Save historical records after each page.
- Write a checkpoint after each successful save.
- Resume collection after interruption.
- Preserve existing historical records.

Retries and enhanced failure logging are scheduled for Day 25.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from opendota_client import fetch_json


RECENT_FILE = Path("data/raw/pro_matches.json")
HISTORY_FILE = Path("data/raw/pro_matches_history.json")
CHECKPOINT_FILE = Path("data/intermediate/backfill_checkpoint.json")

DEFAULT_PAGES = 3
MAX_PAGES = 20


def valid_match_id(value):
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value > 0
    )


def load_json_list(path):
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(f"Expected JSON list: {path}")

    return data


def atomic_save_json(path, data):
    """
    Save JSON using a temporary file followed by replacement.

    The temporary file is created in the same directory
    so os.replace can replace the destination atomically
    on the local filesystem.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = path.with_name(path.name + ".tmp")

    try:
        with temporary_path.open(
            "w", encoding="utf-8"
        ) as file:
            json.dump(data, file, indent=2)
            file.flush()
            os.fsync(file.fileno())

        os.replace(temporary_path, path)

    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def deduplicate_matches(matches):
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


def load_checkpoint():
    if not CHECKPOINT_FILE.exists():
        return None

    with CHECKPOINT_FILE.open(
        "r", encoding="utf-8"
    ) as file:
        checkpoint = json.load(file)

    if not isinstance(checkpoint, dict):
        raise ValueError("Invalid checkpoint format")

    boundary = checkpoint.get("next_boundary")

    if not valid_match_id(boundary):
        raise ValueError("Invalid checkpoint boundary")

    return checkpoint


def save_checkpoint(boundary, total_matches):
    checkpoint = {
        "next_boundary": boundary,
        "total_saved_matches": total_matches,
        "updated_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    atomic_save_json(CHECKPOINT_FILE, checkpoint)


def collect_history(pages):
    if not RECENT_FILE.exists():
        raise FileNotFoundError(
            f"Missing recent match data: {RECENT_FILE}"
        )

    recent = load_json_list(RECENT_FILE)
    history = load_json_list(HISTORY_FILE)

    recent_boundary = oldest_match_id(recent)

    if recent_boundary is None:
        raise ValueError(
            "Recent dataset has no valid match IDs"
        )

    history_boundary = oldest_match_id(history)
    checkpoint = load_checkpoint()

    # The saved historical data is the source of truth.
    # This prevents skipping matches if a checkpoint
    # exists but the corresponding data was not saved.
    boundary = recent_boundary

    if history_boundary is not None:
        boundary = min(boundary, history_boundary)

    if checkpoint is not None:
        checkpoint_boundary = checkpoint["next_boundary"]

        if checkpoint_boundary >= boundary:
            print("[CHECKPOINT] Existing checkpoint found")
        else:
            print(
                "[CHECKPOINT WARNING] Checkpoint is ahead "
                "of saved history; using saved data boundary"
            )

    print(f"Starting before match ID: {boundary}")
    print(f"Previously saved historical matches: {len(history)}")

    newly_collected = 0

    for page_number in range(1, pages + 1):
        print(f"\nFetching historical page {page_number}/{pages}")

        batch = fetch_json(
            "proMatches",
            params={"less_than_match_id": boundary},
        )

        if batch is None:
            raise RuntimeError(
                f"Failed to fetch page {page_number}"
            )

        if not isinstance(batch, list):
            raise ValueError(
                "Unexpected API response: expected list"
            )

        if not batch:
            print("No additional historical matches found.")
            break

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

        next_boundary = oldest_match_id(valid_batch)

        if next_boundary is None or next_boundary >= boundary:
            raise RuntimeError(
                "Pagination did not advance"
            )

        combined = deduplicate_matches(
            history + valid_batch
        )

        combined.sort(
            key=lambda match: match["match_id"],
            reverse=True,
        )

        # Save data BEFORE advancing the checkpoint.
        atomic_save_json(HISTORY_FILE, combined)

        # Only checkpoint successfully saved data.
        save_checkpoint(
            boundary=next_boundary,
            total_matches=len(combined),
        )

        newly_collected += (
            len(combined) - len(history)
        )

        history = combined
        boundary = next_boundary

        print(f"Received records: {len(valid_batch)}")
        print(f"Total saved: {len(history)}")
        print(f"Checkpoint boundary: {boundary}")

    print("\nBackfill summary")
    print(f"New unique matches: {newly_collected}")
    print(f"Total historical matches: {len(history)}")
    print(f"Resume boundary: {boundary}")
    print(f"History file: {HISTORY_FILE}")
    print(f"Checkpoint file: {CHECKPOINT_FILE}")

    return history


def main():
    parser = argparse.ArgumentParser(
        description="Backfill historical Dota 2 professional matches"
    )

    parser.add_argument(
        "--pages",
        type=int,
        default=DEFAULT_PAGES,
        help="Number of pages to fetch",
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
