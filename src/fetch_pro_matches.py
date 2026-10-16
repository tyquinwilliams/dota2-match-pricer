import json
from pathlib import Path

from opendota_client import fetch_json


# ==========================================
# 1. CONFIGURATION
# ==========================================

OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "pro_matches.json"


# ==========================================
# 2. FETCH PROFESSIONAL MATCHES
# ==========================================

def fetch_pro_matches():
    matches = fetch_json("proMatches")

    if matches is None:
        print("Failed to retrieve professional matches.")
        return None

    print(
        f"Successfully retrieved "
        f"{len(matches)} professional matches"
    )

    return matches


# ==========================================
# 3. SAVE RAW DATA
# ==========================================

def save_raw_matches(matches):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(matches, file, indent=2)

    print(f"Saved {len(matches)} matches to {OUTPUT_FILE}")


# ==========================================
# 4. MAIN
# ==========================================

def main():
    matches = fetch_pro_matches()

    if matches is None:
        return

    save_raw_matches(matches)


if __name__ == "__main__":
    main()