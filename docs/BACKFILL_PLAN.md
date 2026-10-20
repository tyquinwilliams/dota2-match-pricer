# Historical Professional Match Backfill Plan

## 1. Objective

Collect historical professional Dota 2 matches to support the open-source match pricing model.

Our initial dataset contains 100 recent matches. This is insufficient for meaningful historical team ratings, opponent-adjusted performance, and model evaluation.

The backfill will expand our dataset while preserving reproducibility and preventing future-data leakage.

## 2. Data Source

**Primary source:** OpenDota API

Endpoint:

`GET https://api.opendota.com/api/proMatches`

The endpoint returns professional match records, including match IDs, timestamps, team IDs, and match outcomes.

Historical pagination will use the `less_than_match_id` parameter, subject to verification against actual API responses.

We will reuse our existing OpenDota client where practical.

## 3. Collection Strategy

Historical data will be collected in batches.

1. Fetch a page of professional matches.
2. Validate the response structure.
3. Extract match IDs and timestamps.
4. Save newly collected matches.
5. Identify the oldest match ID in the batch.
6. Request the next older page.
7. Repeat until the historical boundary is reached.

We will not assume that match IDs perfectly represent chronological order. Actual timestamps will determine historical coverage.

## 4. Initial Backfill Window

**Initial target:** Approximately 90 days of historical professional matches preceding our existing dataset.

The first test will use a much smaller bounded window to verify the pipeline.

Once validated, we can expand toward our longer-term goal of covering recent tournaments and historical team form.

## 5. Raw Data Storage

Existing recent-match data:

`data/raw/pro_matches.json`

Proposed historical storage:

`data/raw/pro_matches_history.json`

Historical records will preserve their original API fields.

Raw files will remain excluded from Git through `.gitignore`.

The intermediate transformation will eventually combine recent and historical records, deduplicate by valid match ID, and sort chronologically.

## 6. Deduplication

Match ID will be the primary deduplication key.

When duplicate match IDs are encountered:

- Prefer the most complete valid record.
- Use deterministic tie-breaking.
- Never discard a unique match solely because it has missing team IDs.
- Preserve records with incomplete identifiers for quality analysis.

The existing `deduplicate_matches()` function provides the starting implementation.

## 7. Checkpoint and Resume

The backfill process must be restartable.

A checkpoint should record:

- Last successfully completed page boundary.
- Number of records collected.
- Historical start and end timestamps.
- Last successful save time.

Checkpoint updates must occur only after the corresponding batch has been safely saved.

After interruption, the process should resume without restarting from the newest match.

## 8. API Reliability

The collector will use:

- Request timeouts.
- Conservative rate limiting.
- Retries with exponential backoff.
- Logging for failed requests.
- Clear stopping conditions.
- Graceful handling of empty or malformed responses.

We will avoid unnecessary repeated API requests.

## 9. Data Quality

Backfilled records will be checked for:

- Valid match IDs.
- Valid timestamps.
- Duplicate match IDs.
- Missing team identifiers.
- Valid match outcomes.
- Historical window coverage.
- Chronological consistency.

Matches with incomplete data will be retained but marked ineligible for Elo where necessary.

## 10. Leakage Prevention

The model will use only information available before the match being priced.

For example:

- Team Elo ratings must be updated chronologically.
- Team form cannot include future matches.
- Roster recovery must use earlier evidence.
- Tournament outcomes cannot influence predictions made before those outcomes occurred.

Historical records may be collected retrospectively, but model features must respect their original information availability.

## 11. Implementation Roadmap

| Day | Task | Deliverable |
|---|---|---|
| 22 | Document historical backfill strategy | `docs/BACKFILL_PLAN.md` |
| 23 | Implement historical match collection | `src/backfill_pro_matches.py` |
| 24 | Add checkpoint and resume | Restart test |
| 25 | Add throttling, retries, and failure logging | Hardened collector |
| 26 | Collect first bounded historical window | Local historical dataset |
| 27 | Validate historical coverage | Coverage report |

## 12. Success Criteria

The historical backfill will be considered successful when:

- Collection reaches a defined historical boundary.
- Match records are stored without unintended data loss.
- Duplicate IDs are handled deterministically.
- Interrupted collection can resume.
- API failures do not corrupt saved data.
- Coverage and quality can be measured.
- Historical records can feed the intermediate match pipeline.

## 13. Open Decisions

Before implementing the collector, confirm:

- The OpenDota endpoint's historical pagination behavior.
- The appropriate request interval and applicable API limits.
- Whether the initial 90-day window provides sufficient professional-match coverage.
- How historical raw data will be merged with the existing recent-match dataset.