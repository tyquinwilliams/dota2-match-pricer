
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

RAW_FILE = Path("data/raw/pro_matches.json")
OUTPUT_FILE = Path("data/intermediate/matches_int.csv")

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
]


def to_utc(timestamp):
    if timestamp is None:
        return None

    return datetime.fromtimestamp(
        timestamp, tz=timezone.utc
    ).isoformat()


def transform_match(match):
    radiant_id = match.get("radiant_team_id")
    dire_id = match.get("dire_team_id")
    radiant_win = match.get("radiant_win")

    has_teams = (
        radiant_id is not None
        and dire_id is not None
        and radiant_id != dire_id
    )

    has_outcome = isinstance(radiant_win, bool)

    eligible = (
        match.get("match_id") is not None
        and match.get("start_time") is not None
        and has_teams
        and has_outcome
    )

    winning_team_id = None

    if has_teams and has_outcome:
        winning_team_id = (
            radiant_id if radiant_win else dire_id
        )

    return {
        "match_id": match.get("match_id"),
        "start_time": match.get("start_time"),
        "start_time_utc": to_utc(match.get("start_time")),
        "duration_seconds": match.get("duration"),
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
    }


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

    transformed.sort(
        key=lambda match: (
            match["start_time"] is None,
            match["start_time"] or 0,
            match["match_id"] or 0,
        )
    )

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

    print(f"Raw matches: {len(raw_matches)}")
    print(f"Intermediate matches: {len(transformed)}")
    print(f"Eligible for Elo: {eligible_count}")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
