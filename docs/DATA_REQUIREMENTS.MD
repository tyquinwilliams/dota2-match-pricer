
# Data Requirements

## 1. Prediction Targets

V1 will predict individual professional Dota 2 game outcomes and derive BO3/BO5 series probabilities from game-level predictions.

Series probabilities will initially assume independent games with constant win probabilities. These assumptions will be evaluated later.

All model features must use information available before the prediction time.

## 2. Historical Data Windows

- Professional matches: last 12 months
- High-MMR public matches: rolling 90 days
- Team, player, and tournament history: within the available 12-month professional dataset
- Patch history: patches represented in collected matches

Historical windows must be configurable.

## 3. Professional Match Data

Required entities and fields:

- Series: series ID, participating teams, format, tournament, scheduled time, series outcome
- Game: match ID, series ID, start time, duration, participating teams, winner, patch
- Team: team ID, name, region
- Player: player ID, team, position, hero, match performance
- Roster: player membership, roster changes, stand-ins
- Tournament: tournament ID, tier, region, LAN/online status, participants
- Draft: hero picks, bans, and pick order where available

## 4. High-MMR Public Match Data

Collect recent high-MMR matches to calculate:

- Hero pick rates and win rates
- Hero performance by role
- Player performance and hero proficiency
- Item build trends
- Patch-specific meta trends

Retain match type and source identifiers to distinguish professional and public matches.

High-MMR outcomes may be evaluated as supplementary training data, but the initial Elo baseline will use professional match results.

## 5. Team Form

Calculate:

- Win rates over the last 5, 10, and 20 games
- Win rates over the last 7, 30, and 90 days
- Winning and losing streaks
- Opponent-adjusted performance
- Historical Elo
- Recent series performance
- Performance with the current roster

## 6. Player and Roster Performance

Maintain separate professional and high-MMR player metrics.

Track:

- Historical team performance
- Performance of the current five-player roster
- Individual player performance
- Player performance by position (1-5)
- Hero pools and hero-specific performance
- Roster continuity and substitutions
- Historical player-to-team membership

Player account linking and missing data must be documented.

## 7. Patch and Meta

Track patch identifiers, release dates, hero statistics, and match dates.

Use historical patch information with greater emphasis on recent matches and the current patch.

The weighting methodology will be determined during model development.

## 8. Tournament Strength

Use both tournament classifications and the historical strength of participating teams.

Candidate fields:

- Tournament tier
- Region
- LAN versus online
- Series format
- Participating teams
- Pre-tournament team Elo
- Derived tournament strength

## 9. Derived Features

Candidate features include:

- Team Elo
- Rolling team form
- Opponent-adjusted strength
- Roster stability
- Player and hero proficiency
- Patch-specific performance
- Tournament strength
- Recent high-MMR meta indicators

These are candidate features, not a commitment to include every feature in the initial model.

## 10. Data Quality and Leakage Prevention

- Preserve source identifiers and timestamps.
- Keep professional and high-MMR data distinguishable.
- Document missing values and incomplete coverage.
- Validate team, player, match, and series relationships.
- Calculate historical features using only information available before prediction time.
- Use chronological backtesting rather than random train/test splitting.

## 11. Open Questions

To investigate during API research:

- Which sources provide reliable professional game and series identifiers?
- How complete is historical professional match coverage?
- Can professional players be reliably linked to high-MMR accounts?
- Are tournament tiers and patch identifiers consistently available?
- What API limits, licensing restrictions, and data gaps exist?
