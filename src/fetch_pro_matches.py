import requests
import json
from pathlib import Path

API_URL = "https://api.opendota.com/api/proMatches"

response = requests.get(API_URL, timeout=15)
response.raise_for_status()

matches = response.json()

print(f"Successfully retrieved {len(matches)} professional matches")

# Create a directory for raw API responses
output_dir = Path("data/raw")
output_dir.mkdir(parents=True, exist_ok=True)

# Save the original API response
output_file = output_dir / "pro_matches.json"

with open(output_file, "w", encoding="utf-8") as file:
    json.dump(matches, file, indent=2)

print(f"Saved {len(matches)} matches to {output_file}")