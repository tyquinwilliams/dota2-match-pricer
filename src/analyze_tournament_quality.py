import json
from pathlib import Path
from collections import defaultdict

# Load our RAW matches
file_path = Path("data/raw/pro_matches.json")

with open(file_path, "r", encoding="utf-8") as file:
    matches = json.load(file)

# Store tournament statistics
tournaments = defaultdict(lambda: {"total": 0, "incomplete": 0})

for match in matches:
    league = match.get("league_name") or "Unknown"

    tournaments[league]["total"] += 1

    # Check if either team ID is missing
    if (
        match.get("radiant_team_id") is None
        or match.get("dire_team_id") is None
    ):
        tournaments[league]["incomplete"] += 1

# Display tournament data quality
print("\n===== TOURNAMENT DATA QUALITY =====")

for league, stats in sorted(
    tournaments.items(),
    key=lambda item: item[1]["incomplete"],
    reverse=True
):
    total = stats["total"]
    incomplete = stats["incomplete"]
    missing_pct = (incomplete / total) * 100

    print(
        f"{league}: "
        f"{total} matches | "
        f"{incomplete} incomplete | "
        f"{missing_pct:.1f}% missing"
    )