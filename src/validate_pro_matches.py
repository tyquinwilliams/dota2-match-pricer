import json
from pathlib import Path

# ==========================================
# 1. LOAD RAW DATA
# ==========================================

file_path = Path("data/raw/pro_matches.json")

with open(file_path, "r", encoding="utf-8") as file:
    matches = json.load(file)

print(f"Total matches: {len(matches)}")


# ==========================================
# 2. CHECK FOR DUPLICATE MATCH IDS
# ==========================================

match_ids = [match["match_id"] for match in matches]

duplicate_count = len(match_ids) - len(set(match_ids))

print(f"Duplicate match IDs: {duplicate_count}")


# ==========================================
# 3. CHECK FOR MISSING REQUIRED FIELDS
# ==========================================

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


# ==========================================
# 4. IDENTIFY MATCHES ELIGIBLE FOR ELO
# ==========================================

valid_matches = [
    match for match in matches
    if match.get("radiant_team_id") is not None
    and match.get("dire_team_id") is not None
]

invalid_matches = len(matches) - len(valid_matches)

print(f"\nMatches usable for Elo: {len(valid_matches)}")
print(f"Matches missing team information: {invalid_matches}")


# ==========================================
# 5. INVESTIGATE INCOMPLETE MATCHES
# ==========================================

incomplete_matches = [
    match for match in matches
    if match.get("radiant_team_id") is None
    or match.get("dire_team_id") is None
]

print("\n===== SAMPLE INCOMPLETE MATCHES =====")

for match in incomplete_matches[:5]:
    print(f"\nMatch ID: {match.get('match_id')}")
    print(f"Tournament: {match.get('league_name')}")
    print(f"Radiant: {match.get('radiant_name')}")
    print(f"Radiant ID: {match.get('radiant_team_id')}")
    print(f"Dire: {match.get('dire_name')}")
    print(f"Dire ID: {match.get('dire_team_id')}")

print("\n===== VALIDATION COMPLETE =====")