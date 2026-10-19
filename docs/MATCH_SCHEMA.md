
# Dota 2 Match Pricer — Canonical Data Schema

## Purpose

Standardize OpenDota match data for ingestion, validation, feature engineering, and pre-match pricing.

V1 uses team Elo as its initial predictive model. Player-level data is retained for historical activity, roster analysis, and future player ratings.

## 1. matches_int

**Grain:** One row per professional game.

| Column | Type | Description |
|---|---|---|
| match_id | BIGINT | Unique match identifier |
| start_time | BIGINT | Unix timestamp in seconds |
| start_time_utc | TIMESTAMP | UTC match start |
| duration_seconds | INTEGER | Game duration |
| radiant_team_id | BIGINT, nullable | Radiant team |
| dire_team_id | BIGINT, nullable | Dire team |
| radiant_team_name | STRING, nullable | Radiant name |
| dire_team_name | STRING, nullable | Dire name |
| league_id | BIGINT, nullable | Tournament ID |
| league_name | STRING, nullable | Tournament name |
| series_id | BIGINT, nullable | Series identifier |
| series_type | INTEGER, nullable | Series format code |
| radiant_score | INTEGER, nullable | Radiant kills |
| dire_score | INTEGER, nullable | Dire kills |
| radiant_win | BOOLEAN | Game outcome |
| winning_team_id | BIGINT, nullable | Derived winner |
| team_id_source | STRING | original, recovered, mixed, or unresolved |
| eligible_for_team_elo | BOOLEAN | Whether game has usable team IDs and outcome |

**Primary key:** `match_id`

Raw team IDs must never be overwritten by inferred IDs. Recovery evidence must remain traceable.

## 2. player_matches_int

**Grain:** One row per player per game.

| Column | Type | Description |
|---|---|---|
| match_id | BIGINT | Match identifier |
| player_slot | INTEGER | Match-specific player slot |
| account_id | BIGINT, nullable | Persistent player account ID |
| team_side | STRING | radiant or dire |
| team_id | BIGINT, nullable | Associated team |
| hero_id | INTEGER, nullable | Hero selected |
| kills | INTEGER, nullable | Kills |
| deaths | INTEGER, nullable | Deaths |
| assists | INTEGER, nullable | Assists |
| last_hits | INTEGER, nullable | Last hits |
| denies | INTEGER, nullable | Denies |
| gold_per_min | INTEGER, nullable | GPM |
| xp_per_min | INTEGER, nullable | XPM |
| hero_damage | INTEGER, nullable | Hero damage |
| tower_damage | INTEGER, nullable | Tower damage |
| hero_healing | INTEGER, nullable | Hero healing |
| net_worth | INTEGER, nullable | Final net worth |
| lane_role | INTEGER, nullable | Lane role |
| position_est | STRING, nullable | Estimated position, normalized |
| win | BOOLEAN, nullable | Player's team won |
| start_time | BIGINT | Match timestamp |

**Primary key:** `(match_id, player_slot)`

An account ID may be missing or anonymized. `player_slot` is not a persistent player identifier.

## 3. team_rosters_int

**Grain:** One player-team appearance per match.

| Column | Type | Description |
|---|---|---|
| match_id | BIGINT | Match identifier |
| start_time | BIGINT | Match start |
| team_id | BIGINT, nullable | Team identifier |
| account_id | BIGINT, nullable | Player identifier |
| player_slot | INTEGER | Match-specific slot |
| hero_id | INTEGER, nullable | Hero |
| team_side | STRING | radiant or dire |
| roster_identity_status | STRING | identified, partial, or unknown |

**Unique key:** `(match_id, player_slot)`

## 4. Planned Player Features

Historical features calculated before each match:

- Career professional match count
- Professional matches in the last 30 and 90 days
- Recent team appearances
- Roster continuity
- Historical average KDA
- Historical GPM and XPM
- Hero-specific match counts and win rates
- Individual player Elo ratings (V2)
- Player-adjusted team probabilities (V2)

Player performance from the target match must never be included in its pre-match prediction.

## 5. Data Quality Rules

1. Each match ID is unique.
2. Each player slot is unique within a match.
3. A complete standard game should contain 10 player records.
4. Player and roster records must reference an existing match.
5. Missing team or account IDs remain missing unless supported by recovery evidence.
6. Raw OpenDota responses remain unchanged.
7. Historical features must exclude the target game and later games.
8. Elo ratings update only after the relevant match outcome.
9. Post-game performance metrics are never direct pre-match inputs for the same game.
10. Missing or ambiguous team identities must be flagged.

## 6. Implementation Roadmap

- Day 15: Define canonical match and player schemas.
- Day 16: Implement raw-to-intermediate match transformation.
- Days 17–21: Improve timestamps, team identities, ordering, and intermediate exports.
- Later milestones: Historical player activity, roster continuity, quality tests, Elo modeling, and series pricing.

## 7. Data Sources

OpenDota API:

- `/proMatches` — professional match summaries
- `/matches/{match_id}` — detailed match and player statistics

The detailed endpoint is required for player-level performance data.
