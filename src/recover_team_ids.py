import requests

# ==========================================
# 1. CONFIGURATION
# ==========================================

MATCH_ID = 9040915797

reference_matches = [
    9040873491,  # PIZZA HOOK
    9040842945,  # La Manada
]


# ==========================================
# 2. FETCH MATCH DATA
# ==========================================

def fetch_match(match_id):
    url = f"https://api.opendota.com/api/matches/{match_id}"

    response = requests.get(url, timeout=20)
    response.raise_for_status()

    return response.json()


# ==========================================
# 3. EXTRACT PLAYER ROSTERS
# ==========================================

def get_match_rosters(match):
    radiant_players = set()
    dire_players = set()

    for player in match.get("players", []):
        account_id = player.get("account_id")
        player_slot = player.get("player_slot")

        if account_id is None or player_slot is None:
            continue

        if player_slot < 128:
            radiant_players.add(account_id)
        else:
            dire_players.add(account_id)

    return radiant_players, dire_players


# ==========================================
# 4. LOAD TARGET MATCH
# ==========================================

match = fetch_match(MATCH_ID)

radiant, dire = get_match_rosters(match)

print(f"Match: {MATCH_ID}")
print(f"Radiant player IDs: {sorted(radiant)}")
print(f"Dire player IDs: {sorted(dire)}")


# ==========================================
# 5. COMPARE AGAINST IDENTIFIED TEAMS
# ==========================================

print("\n===== TEAM ID RECOVERY =====")

for reference_id in reference_matches:

    reference = fetch_match(reference_id)

    reference_radiant, reference_dire = get_match_rosters(reference)

    reference_teams = [
        (
            "Radiant",
            reference_radiant,
            reference.get("radiant_team_id"),
            reference.get("radiant_name"),
        ),
        (
            "Dire",
            reference_dire,
            reference.get("dire_team_id"),
            reference.get("dire_name"),
        ),
    ]

    for side, roster, team_id, team_name in reference_teams:

        # Ignore reference teams without registered IDs
        if team_id is None:
            continue

        # Require a complete five-player roster
        if len(roster) != 5:
            continue

        # Compare with target Radiant roster
        if len(radiant) == 5 and radiant == roster:
            print(
                f"Recovered Radiant candidate: "
                f"{team_name} (Team ID: {team_id})"
            )

        # Compare with target Dire roster
        if len(dire) == 5 and dire == roster:
            print(
                f"Recovered Dire candidate: "
                f"{team_name} (Team ID: {team_id})"
            )


print("\n===== RECOVERY COMPLETE =====")