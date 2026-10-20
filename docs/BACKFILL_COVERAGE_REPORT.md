# Historical Professional Match Coverage Report

**Project:** Dota 2 Open-Source Match Pricer  
**Roadmap:** Day 27  
**Dataset:** `data/raw/pro_matches_history.json`

## 1. Executive Summary

The first historical backfill collected 800 professional Dota 2 matches spanning September 5 through October 16, 2026.

All 800 records have unique match IDs. However, 72 records (9%) have at least one missing team identifier, and six calendar days within the observed period contain no matches.

The dataset is suitable for further processing and quality analysis, but it is not yet sufficient to establish reliable model performance.

## 2. Dataset Statistics

| Metric | Result |
|---|---:|
| Total historical matches | 800 |
| Unique match IDs | 800 |
| Duplicate records | 0 |
| Matches missing team IDs | 72 |
| Missing team ID rate | 9.0% |
| Matches not flagged for missing IDs | 728 |
| Calendar days in observed range | 42 |
| Days with recorded matches | 36 |
| Days without recorded matches | 6 |

**Historical range:** September 5 – October 16, 2026 (UTC).

The 728 matches without missing-team-ID flags are not necessarily all Elo-eligible. Timestamp, duration, outcome, and team-identity validity must also be checked.

## 3. Coverage Gaps

No historical records were observed for:

- September 14–17, 2026
- September 28, 2026
- October 4, 2026

These dates should not automatically be classified as missing API data. Professional match activity may have been absent or lower during tournament breaks.

Additional verification is needed to establish whether the backfill is complete for those dates.

## 4. Team Identity Quality

72 of 800 historical matches (9%) have missing team identifiers according to the initial audit.

These records should be retained in raw storage.

Our existing team ID recovery policy requires evidence from earlier matches, exact five-player roster matches, and explicit handling of ambiguous identities.

Unresolved matches must remain excluded from team-based Elo calculations.

## 5. Collection Reliability

The historical backfill completed with:

- No duplicate match IDs in the saved dataset.
- Successful pagination using `less_than_match_id`.
- Checkpoint and resume support.
- Atomic saves after completed pages.
- API throttling, retries, and structured failure logging.

The audit did not independently verify the completeness of OpenDota's historical coverage.

## 6. Modeling Implications

Before using this dataset for pricing:

1. Combine historical and recent match records without duplicating match IDs.
2. Apply the existing intermediate transformation and validation rules.
3. Preserve chronological ordering.
4. Exclude matches that fail Elo eligibility checks.
5. Calculate team ratings using only information available before each match.
6. Evaluate model performance using chronological train/test splits.

## 7. Next Steps

The historical dataset provides a foundation for the next phase of development.

Priorities include integrating historical records into the intermediate pipeline, measuring Elo-eligible match counts, and eventually collecting enough history to support meaningful team-rating initialization and evaluation.

## 8. Conclusion

**Day 27 coverage audit: Completed.**

The historical collection contains 800 unique matches across 36 observed match days.

The main identified quality concern is missing team identity information in 9% of records.

The dataset is ready for the next stage of transformation and validation, with coverage completeness and model readiness remaining open questions.