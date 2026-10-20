
import csv
import sys
from collections import Counter
from pathlib import Path

INPUT_FILE = Path("data/intermediate/matches_int.csv")

REQUIRED_COLUMNS = [
    "match_id",
    "start_time",
    "duration_seconds",
    "radiant_team_id_effective",
    "dire_team_id_effective",
    "radiant_win",
    "winning_team_id",
    "eligible_for_team_elo",
    "validation_issues",
]


def validate():
    if not INPUT_FILE.exists():
        raise ValueError(f"Missing file: {INPUT_FILE}")

    with INPUT_FILE.open(
        "r", newline="", encoding="utf-8"
    ) as file:
        reader = csv.DictReader(file)

        missing_columns = set(REQUIRED_COLUMNS) - set(
            reader.fieldnames or []
        )

        if missing_columns:
            raise ValueError(
                f"Missing columns: {sorted(missing_columns)}"
            )

        rows = list(reader)

    if not rows:
        raise ValueError("Intermediate dataset is empty")

    ids = [row["match_id"] for row in rows]
    counts = Counter(ids)

    duplicates = [
        match_id
        for match_id, count in counts.items()
        if count > 1
    ]

    if duplicates:
        raise ValueError(
            f"Duplicate match IDs: {duplicates}"
        )

    timestamps = [
        int(row["start_time"])
        for row in rows
        if row["start_time"]
    ]

    if timestamps != sorted(timestamps):
        raise ValueError(
            "Matches are not chronologically ordered"
        )

    eligible_count = 0

    for row in rows:
        if row["eligible_for_team_elo"] != "True":
            continue

        eligible_count += 1

        radiant = int(row["radiant_team_id_effective"])
        dire = int(row["dire_team_id_effective"])
        winner = int(row["winning_team_id"])

        assert radiant > 0
        assert dire > 0
        assert radiant != dire
        assert winner in (radiant, dire)
        assert row["radiant_win"] in ("True", "False")
        assert int(row["start_time"]) > 0
        assert int(row["duration_seconds"]) > 0
        assert not row["validation_issues"]

    print("PASS: Intermediate dataset validation")
    print(f"Total matches: {len(rows)}")
    print(f"Unique match IDs: {len(counts)}")
    print(f"Elo eligible: {eligible_count}")
    print(f"Elo excluded: {len(rows) - eligible_count}")


if __name__ == "__main__":
    try:
        validate()
    except (ValueError, AssertionError) as error:
        print(f"FAIL: {error}")
        sys.exit(1)
