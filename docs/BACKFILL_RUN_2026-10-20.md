# Historical Backfill Run — October 20, 2026

## Objective

Collect a bounded historical sample of professional Dota 2 matches preceding the recent-match dataset.

**Target:** Reach October 1, 2026.

## Collection Results

| Metric | Result |
|---|---|
| Historical matches collected | 800 |
| Earliest match | 2026-09-05 20:48:32 UTC |
| Latest match | 2026-10-16 13:46:12 UTC |
| Oldest match ID | 8984703068 |
| API failures observed | 0 |
| Target boundary reached | Yes |

## Data Storage

Historical matches are stored locally at:

`data/raw/pro_matches_history.json`

Checkpoint state is stored at:

`data/intermediate/backfill_checkpoint.json`

These files are excluded from Git.

## Collection Method

Historical matches were retrieved using the OpenDota `proMatches` endpoint with `less_than_match_id` pagination.

The backfill pipeline supports caching, request throttling, retries, structured error logging, atomic saves, and checkpoint recovery.

## Next Steps

Day 27 will validate historical coverage, match counts, duplicate IDs, missing team identifiers, and overall data quality before incorporating historical records into the intermediate modeling pipeline.