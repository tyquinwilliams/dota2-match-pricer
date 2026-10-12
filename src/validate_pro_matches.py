import json
from pathlib import Path

# Load our saved RAW data
file_path = Path("data/raw/pro_matches.json")

with open(file_path, "r", encoding="utf-8") as file:
    matches = json.load(file)

print(f"Total matches: {len(matches)}")

# Check for duplicate match IDs
match_ids = [match["match_id"] for match in matches]
duplicate_count = len(match_ids) - len(set(match_ids))

print(f"Duplicate match IDs: {duplicate_count}")

# Check for missing required fields
required_fields = [
    "match_id",
    "start_time",
    "radiant_team_id",
    "dire_team_id",
    "radiant_win",
]

for field in required_fields:
    missing_count = sum(
        1 for match in matches
        if match.get(field) is None
    )

    print(f"Missing {field}: {missing_count}")

# Count matches with both team IDs present
valid_matches = [
    match for match in matches
    if match.get("radiant_team_id") is not None
    and match.get("dire_team_id") is not None
]

invalid_matches = len(matches) - len(valid_matches)

print(f"Matches usable for Elo: {len(valid_matches)}")
print(f"Matches missing team information: {invalid_matches}")