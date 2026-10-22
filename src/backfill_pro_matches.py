
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from opendota_client import fetch_json


ROOT = Path(__file__).resolve().parents[1]
RECENT_FILE = ROOT / "data/raw/pro_matches.json"
BATCH_DIR = ROOT / "data/raw/pro_matches_history"
CHECKPOINT_FILE = ROOT / "data/intermediate/backfill_checkpoint.json"
SNAPSHOT_DIR = ROOT / "data/snapshots"

DEFAULT_START_DATE = "2023-01-01"
BATCH_SIZE = 100


def write_json_atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")

    with temporary.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    os.replace(temporary, path)


def read_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def match_id(match):
    try:
        return int(match["match_id"])
    except (KeyError, TypeError, ValueError):
        return None


def match_date(match):
    try:
        timestamp = int(match["start_time"])
        return datetime.fromtimestamp(
            timestamp, tz=timezone.utc
        ).date()
    except (KeyError, TypeError, ValueError, OverflowError, OSError):
        return None


def load_recent():
    if not RECENT_FILE.exists():
        raise FileNotFoundError(
            f"Missing recent matches: {RECENT_FILE}"
        )

    matches = read_json(RECENT_FILE)

    if not isinstance(matches, list):
        raise ValueError("Recent matches must be a JSON list.")

    valid = [m for m in matches if match_id(m) is not None]

    if not valid:
        raise ValueError("No valid recent match IDs found.")

    return valid


def batch_files():
    return sorted(BATCH_DIR.glob("batch_*.json"))


def load_history():
    history = {}

    for path in batch_files():
        matches = read_json(path)

        if not isinstance(matches, list):
            raise ValueError(f"Invalid batch file: {path}")

        for match in matches:
            mid = match_id(match)

            if mid is None:
                raise ValueError(
                    f"Match without valid ID in {path}"
                )

            if mid in history and history[mid] != match:
                raise ValueError(
                    f"Conflicting match ID {mid} in {path}"
                )

            history[mid] = match

    return history


def next_batch_number():
    numbers = []

    for path in batch_files():
        try:
            numbers.append(int(path.stem.split("_")[-1]))
        except ValueError:
            raise ValueError(f"Invalid batch filename: {path}")

    return max(numbers, default=0) + 1


def save_checkpoint(history, cursor, target):
    dates = [
        match_date(m)
        for m in history.values()
        if match_date(m) is not None
    ]

    write_json_atomic(
        CHECKPOINT_FILE,
        {
            "historical_matches": len(history),
            "last_match_id": cursor,
            "oldest_date": (
                min(dates).isoformat() if dates else None
            ),
            "target_date": target.isoformat(),
            "updated_at": datetime.now(
                timezone.utc
            ).isoformat(),
        },
    )


def verify():
    history = load_history()
    matches = list(history.values())
    dates = [match_date(m) for m in matches]
    known_dates = [d for d in dates if d is not None]

    print("\n[VERIFICATION]")
    print(f"Batch files: {len(batch_files())}")
    print(f"Unique historical matches: {len(history)}")
    print(f"Missing dates: {len(matches) - len(known_dates)}")

    if known_dates:
        print(f"Earliest match: {min(known_dates)}")
        print(f"Latest match: {max(known_dates)}")

    if matches:
        print(f"Oldest match ID: {min(history)}")
        print(f"Newest match ID: {max(history)}")

    print("Verification completed.")
    return history


def create_snapshots():
    history = verify()

    if not history:
        print("No historical matches available.")
        return

    by_year = {}

    for match in history.values():
        date = match_date(match)

        if date is None:
            raise ValueError(
                "Cannot publish snapshots with missing dates."
            )

        by_year.setdefault(date.year, []).append(match)

    for year, matches in sorted(by_year.items()):
        matches.sort(
            key=lambda m: match_id(m),
            reverse=True,
        )

        output = (
            SNAPSHOT_DIR / f"pro_matches_{year}.json"
        )

        write_json_atomic(output, matches)

        print(
            f"[SNAPSHOT] {output.relative_to(ROOT)} "
            f"({len(matches)} matches)"
        )

    print("\nSnapshots created. Not yet committed to Git.")


def backfill(pages, target):
    recent = load_recent()
    history = load_history()

    recent_ids = {
        match_id(m) for m in recent
    }

    if history:
        cursor = min(history)
    else:
        cursor = min(recent_ids)

    print("\n[BACKFILL]")
    print(f"Existing historical matches: {len(history)}")
    print(f"Starting cursor: {cursor}")
    print(f"Target date: {target}")
    print(f"Maximum pages this run: {pages}")

    batch_number = next_batch_number()

    for page in range(1, pages + 1):
        print(f"\n[PAGE {page}/{pages}]")

        response = fetch_json(
            "proMatches",
            params={"less_than_match_id": cursor},
        )

        if not isinstance(response, list):
            print("[STOP] API returned an invalid response.")
            break

        if not response:
            print("[STOP] No more matches returned.")
            break

        valid = [
            m for m in response
            if match_id(m) is not None
        ]

        if not valid:
            print("[STOP] No valid match IDs returned.")
            break

        next_cursor = min(match_id(m) for m in valid)

        if next_cursor >= cursor:
            print("[STOP] Pagination cursor did not advance.")
            break

        new_matches = []
        reached_target = False

        for match in valid:
            mid = match_id(match)
            date = match_date(match)

            if date is None:
                raise ValueError(
                    f"Missing date for match {mid}; "
                    "stopping to avoid an incomplete backfill."
                )

            if date < target:
                reached_target = True
                continue

            if mid not in history and mid not in recent_ids:
                history[mid] = match
                new_matches.append(match)

        if new_matches:
            output = (
                BATCH_DIR /
                f"batch_{batch_number:06d}.json"
            )

            write_json_atomic(output, new_matches)
            batch_number += 1

        cursor = next_cursor
        save_checkpoint(history, cursor, target)

        print(f"API records: {len(response)}")
        print(f"New matches: {len(new_matches)}")
        print(f"Total historical matches: {len(history)}")

        dates = [
            match_date(m)
            for m in valid
            if match_date(m) is not None
        ]

        if dates:
            print(f"Oldest date on page: {min(dates)}")

        if reached_target:
            print(f"[TARGET REACHED] {target}")
            break

        if page < pages:
            time.sleep(1)

    print("\n[RUN COMPLETE]")
    print(f"Historical matches saved: {len(history)}")
    print(f"Next cursor: {cursor}")


def main():
    parser = argparse.ArgumentParser(
        description="Backfill historical Dota 2 professional matches"
    )

    parser.add_argument(
        "--pages",
        type=int,
        default=1,
        help="Maximum number of API pages to fetch",
    )

    parser.add_argument(
        "--start-date",
        default=DEFAULT_START_DATE,
        help="Oldest date to include, YYYY-MM-DD",
    )

    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify saved historical batches",
    )

    parser.add_argument(
        "--snapshot",
        action="store_true",
        help="Create yearly JSON snapshots",
    )

    args = parser.parse_args()

    if args.verify:
        verify()
        return

    if args.snapshot:
        create_snapshots()
        return

    if not 1 <= args.pages <= 20:
        parser.error("--pages must be between 1 and 20")

    try:
        target = datetime.strptime(
            args.start_date, "%Y-%m-%d"
        ).date()
    except ValueError:
        parser.error(
            "--start-date must use YYYY-MM-DD"
        )

    backfill(args.pages, target)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)
