import requests

API_URL = "https://api.opendota.com/api/proMatches"

response = requests.get(API_URL, timeout=15)
response.raise_for_status()

matches = response.json()

print(f"Successfully retrieved {len(matches)} professional matches")