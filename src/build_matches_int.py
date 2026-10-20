
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

RAW_FILE = Path("data/raw/pro_matches.json")
RECOVERY_FILE = Path("data/intermediate/team_id_recovery.csv")
OUTPUT_FILE = Path("data/intermediate/matches_int.csv")

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
    "radiant_team_id_effective",
    "dire_team_id_effective",
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


# ==========================================
# 1. VALIDATION HELPERS
# ==========================================

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


def parse_positive_int(value):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None

    return parsed if parsed > 0 else None


# ==========================================
# 2. DETERMINISTIC DEDUPLICATION
# ==========================================

def record_quality(match):
    """Rank records by validity and completeness."""
    important_fields = [
        "start_time",
        "duration",
        "radiant_team_id",
        "dire_team_id",
        "radiant_win",
        "radiant_score",
        "dire_score",
        "leagueid",
        "series_id",
    ]

    populated_fields = sum(
        match.get(field) is not None
        for field in important_fields
    )

    radiant_id = match.get("radiant_team_id")
    dire_id = match.get("dire_team_id")

    valid_teams = (
        valid_positive_int(radiant_id)
        and valid_positive_int(dire_id)
        and radiant_id != dire_id
    )

    return (
        int(valid_teams),
        int(isinstance(match.get("radiant_win"), bool)),
        int(valid_timestamp(match.get("start_time"))),
        int(valid_positive_int(match.get("duration"))),
        populated_fields,
    )


def record_fingerprint(match):
    """Stable tie-breaker independent of input order."""
    return json.dumps(
        match,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def sort_raw_match(match):
    """Deterministic chronological ordering for raw matches."""
    timestamp = match.get("start_time")
    match_id = match.get("match_id")

    return (
        not valid_timestamp(timestamp),
        timestamp if valid_timestamp(timestamp) else 0,
        match_id if valid_positive_int(match_id) else 0,
        record_fingerprint(match),
    )


def deduplicate_matches(matches):
    """
    Keep the highest-quality record for each valid match ID.

    Records with invalid IDs remain available for validation.
    Results are deterministic regardless of input order.
    """
    best_by_id = {}
    invalid_id_records = []

    for match in matches:
        match_id = match.get("match_id")

        if not valid_positive_int(match_id):
            invalid_id_records.append(match)
            continue

        existing = best_by_id.get(match_id)

        if existing is None:
            best_by_id[match_id] = match
            continue

        candidate_rank = (
            record_quality(match),
            record_fingerprint(match),
        )

        existing_rank = (
            record_quality(existing),
            record_fingerprint(existing),
        )

        if candidate_rank > existing_rank:
            best_by_id[match_id] = match

    unique_matches = (
        list(best_by_id.values())
        + invalid_id_records
    )

    return sorted(unique_matches, key=sort_raw_match)


# ==========================================
# 3. RECOVERED TEAM IDENTITIES
# ==========================================

def load_recoveries(raw_matches):
    if not RECOVERY_FILE.exists():
        return {}

    matches_by_id = {
        match["match_id"]: match
        for match in raw_matches
        if valid_positive_int(match.get("match_id"))
    }

    recoveries = {}

    with RECOVERY_FILE.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            target_id = parse_positive_int(
                row.get("target_match_id")
            )
            reference_id = parse_positive_int(
                row.get("reference_match_id")
            )
            candidate_id = parse_positive_int(
                row.get("team_id_candidate")
            )
            matched_players = parse_positive_int(
                row.get("matched_players")
            )

            side = (row.get("side") or "").strip().lower()
            status = (
                row.get("recovery_status") or ""
            ).strip().lower()

            if (
                target_id is None
                or reference_id is None
                or candidate_id is None
                or matched_players != 5
                or side not in ("radiant", "dire")
                or status != "accepted"
            ):
                continue

            target = matches_by_id.get(target_id)
            reference = matches_by_id.get(reference_id)

            if target is None or reference is None:
                continue

            target_time = target.get("start_time")
            reference_time = reference.get("start_time")

            if (
                not valid_timestamp(target_time)
                or not valid_timestamp(reference_time)
                or reference_time >= target_time
            ):
                continue

            key = (target_id, side)
            recoveries.setdefault(key, set()).add(
                candidate_id
            )

    return recoveries


def effective_team_id(original_id, recovery_candidates):
    if valid_positive_int(original_id):
        return original_id, "original"

    if len(recovery_candidates) == 1:
        return next(iter(recovery_candidates)), "recovered"

    if len(recovery_candidates) > 1:
        return None, "ambiguous"

    return None, "unresolved"


# ==========================================
# 4. MATCH TRANSFORMATION
# ==========================================

def transform_match(match, recoveries=None):
    recoveries = recoveries or {}
    issues = []

    match_id = match.get("match_id")
    start_time = match.get("start_time")
    duration = match.get("duration")

    radiant_id = match.get("radiant_team_id")
    dire_id = match.get("dire_team_id")
    radiant_win = match.get("radiant_win")

    radiant_effective, radiant_source = effective_team_id(
        radiant_id,
        recoveries.get((match_id, "radiant"), set()),
    )

    dire_effective, dire_source = effective_team_id(
        dire_id,
        recoveries.get((match_id, "dire"), set()),
    )

    if not valid_positive_int(match_id):
        issues.append("missing_or_invalid_match_id")

    if not valid_timestamp(start_time):
        issues.append("missing_or_invalid_timestamp")

    if not valid_positive_int(duration):
        issues.append("missing_or_invalid_duration")

    has_teams = (
        valid_positive_int(radiant_effective)
        and valid_positive_int(dire_effective)
        and radiant_effective != dire_effective
    )

    if not has_teams:
        issues.append("missing_or_invalid_team_id")

    if (
        radiant_source == "ambiguous"
        or dire_source == "ambiguous"
    ):
        issues.append("ambiguous_team_identity")

    has_outcome = isinstance(radiant_win, bool)

    if not has_outcome:
        issues.append("missing_or_invalid_outcome")

    eligible = len(issues) == 0

    winning_team_id = None

    if has_teams and has_outcome:
        winning_team_id = (
            radiant_effective if radiant_win
            else dire_effective
        )

    if radiant_source == dire_source:
        team_id_source = radiant_source
    else:
        team_id_source = (
            f"radiant:{radiant_source};dire:{dire_source}"
        )

    return {
        "match_id": match_id,
        "start_time": start_time,
        "start_time_utc": to_utc(start_time),
        "duration_seconds": duration,
        "radiant_team_id": radiant_id,
        "dire_team_id": dire_id,
        "radiant_team_id_effective": radiant_effective,
        "dire_team_id_effective": dire_effective,
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
        "team_id_source": team_id_source,
        "eligible_for_team_elo": eligible,
        "validation_issues": ";".join(issues),
    }


# ==========================================
# 5. INTERMEDIATE SORTING
# ==========================================

def sort_key(match):
    timestamp = match["start_time"]
    match_id = match["match_id"]

    return (
        not valid_timestamp(timestamp),
        timestamp if valid_timestamp(timestamp) else 0,
        match_id if valid_positive_int(match_id) else 0,
        record_fingerprint(match),
    )


# ==========================================
# 6. PIPELINE
# ==========================================

def main():
    if not RAW_FILE.exists():
        print(f"Missing raw file: {RAW_FILE}")
        return

    with RAW_FILE.open("r", encoding="utf-8") as file:
        raw_matches = json.load(file)

    unique_matches = deduplicate_matches(raw_matches)

    duplicates_removed = (
        len(raw_matches) - len(unique_matches)
    )

    recoveries = load_recoveries(unique_matches)

    transformed = [
        transform_match(match, recoveries)
        for match in unique_matches
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
    print(f"Duplicate records removed: {duplicates_removed}")
    print(f"Intermediate matches: {len(transformed)}")
    print(f"Eligible for Elo: {eligible_count}")
    print(
        f"Ineligible for Elo: "
        f"{len(transformed) - eligible_count}"
    )

    print("\nValidation issues:")

    if issue_counts:
        for issue, count in sorted(issue_counts.items()):
            print(f"  {issue}: {count}")
    else:
        print("  None")

    print(f"\nSaved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
