
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

RAW_FILE = Path("data/raw/pro_matches.json")
OUTPUT_FILE = Path("data/intermediate/matches_int.csv")

# Reject timestamps earlier than Dota 2's release year.
MIN_TIMESTAMP = int(
    datetime(2013, 1, 1, tzinfo=timezone.utc).timestamp()
)

FIELDS = [
    "match_id",
    "start_time",
    "start_time_utc",
    "duration_seconds",
    "radiant_team_id",
    "dire_team_id",
    "radiant_team_name",
    "dire_team_name",
    "league_id",
    "league_name",
    "series_id",
    "series_type",
    "radiant_score",
    "dire_score",
    "radiant_win",
    "winning_team_id",
    "team_id_source",
    "eligible_for_team_elo",
    "validation_issues",
]


def valid_positive_int(value):
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value > 0
    )


def valid_timestamp(value):
    if not valid_positive_int(value):
        return False

    if value < MIN_TIMESTAMP:
        return False

    try:
        datetime.fromtimestamp(value, tz=timezone.utc)
        return True
    except (ValueError, OverflowError, OSError):
        return False


def to_utc(timestamp):
    if not valid_timestamp(timestamp):
        return None

    return datetime.fromtimestamp(
        timestamp, tz=timezone.utc
    ).isoformat()


def transform_match(match):
    issues = []

    match_id = match.get("match_id")
    start_time = match.get("start_time")
    duration = match.get("duration")

    radiant_id = match.get("radiant_team_id")
    dire_id = match.get("dire_team_id")
    radiant_win = match.get("radiant_win")

    if not valid_positive_int(match_id):
        issues.append("missing_or_invalid_match_id")

    if not valid_timestamp(start_time):
        issues.append("missing_or_invalid_timestamp")

    if not valid_positive_int(duration):
        issues.append("missing_or_invalid_duration")

    has_teams = (
        valid_positive_int(radiant_id)
        and valid_positive_int(dire_id)
        and radiant_id != dire_id
    )

    if not has_teams:
        issues.append("missing_or_invalid_team_id")

    has_outcome = isinstance(radiant_win, bool)

    if not has_outcome:
        issues.append("missing_or_invalid_outcome")

    eligible = len(issues) == 0

    winning_team_id = None

    if has_teams and has_outcome:
        winning_team_id = (
            radiant_id if radiant_win else dire_id
        )

    return {
        "match_id": match_id,
        "start_time": start_time,
        "start_time_utc": to_utc(start_time),
        "duration_seconds": duration,
        "radiant_team_id": radiant_id,
        "dire_team_id": dire_id,
        "radiant_team_name": match.get("radiant_name"),
        "dire_team_name": match.get("dire_name"),
        "league_id": match.get("leagueid"),
        "league_name": match.get("league_name"),
        "series_id": match.get("series_id"),
        "series_type": match.get("series_type"),
        "radiant_score": match.get("radiant_score"),
        "dire_score": match.get("dire_score"),
        "radiant_win": radiant_win,
        "winning_team_id": winning_team_id,
        "team_id_source": (
            "original" if has_teams else "unresolved"
        ),
        "eligible_for_team_elo": eligible,
        "validation_issues": ";".join(issues),
    }


def sort_key(match):
    timestamp = match["start_time"]
    match_id = match["match_id"]

    return (
        not valid_timestamp(timestamp),
        timestamp if valid_timestamp(timestamp) else 0,
        match_id if valid_positive_int(match_id) else 0,
    )


def main():
    if not RAW_FILE.exists():
        print(f"Missing raw file: {RAW_FILE}")
        return

    with RAW_FILE.open("r", encoding="utf-8") as file:
        raw_matches = json.load(file)

    transformed = [
        transform_match(match)
        for match in raw_matches
    ]

    transformed.sort(key=sort_key)

    OUTPUT_FILE.parent.mkdir(
        parents=True, exist_ok=True
    )

    with OUTPUT_FILE.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=FIELDS
        )
        writer.writeheader()
        writer.writerows(transformed)

    eligible_count = sum(
        match["eligible_for_team_elo"]
        for match in transformed
    )

    issue_counts = Counter()

    for match in transformed:
        if match["validation_issues"]:
            issue_counts.update(
                match["validation_issues"].split(";")
            )

    print(f"Raw matches: {len(raw_matches)}")
    print(f"Intermediate matches: {len(transformed)}")
    print(f"Eligible for Elo: {eligible_count}")
    print(f"Ineligible for Elo: {len(transformed) - eligible_count}")

    print("\nValidation issues:")

    if issue_counts:
        for issue, count in sorted(issue_counts.items()):
            print(f"  {issue}: {count}")
    else:
        print("  None")

    print(f"\nSaved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
