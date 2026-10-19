# Dota 2 Match Pricer — 60-Day Roadmap

> **Reconstructed October 19, 2026.** Days 1–14 summarize completed work. Days 15–60 are a reconstructed forward plan, not a verbatim copy of the original chat. Once reviewed and committed, this file is the canonical roadmap.

## Goal

Build an open-source, reproducible **pre-match** Dota 2 pricing model: collect professional matches, normalize team and roster history, create leakage-safe features, estimate game win probabilities with Elo, derive BO3/BO5 series probabilities, and compare fair prices with market odds. No in-play modeling in v1.

## Rules

- One project day means one milestone, not necessarily one calendar day.
- Make a Git commit for each completed milestone.
- Keep raw inputs and API caches gitignored; commit code, documentation, tests and small safe examples.
- Use only information available before each match starts for features and ratings.
- Favor free local Python tooling for v1; Snowflake or orchestration can be added later.
- Document any scope or schedule changes here before implementing them.

## Daily plan

- [x] **Day 01: Define project goal and initialize repository.** Deliverable: README and first commit.
- [x] **Day 02: Write project overview.** Deliverable: Project overview document.
- [x] **Day 03: Specify modeling data requirements.** Deliverable: Data requirements document.
- [x] **Day 04: Evaluate and document data sources.** Deliverable: Data sources document.
- [x] **Day 05: Build initial OpenDota professional-match fetch.** Deliverable: src/fetch_pro_matches.py.
- [x] **Day 06: Persist raw professional matches locally.** Deliverable: data/raw/pro_matches.json (gitignored).
- [x] **Day 07: Implement raw match validation.** Deliverable: src/validate_pro_matches.py.
- [x] **Day 08: Assess tournament-level missing team IDs.** Deliverable: src/analyze_tournament_quality.py.
- [x] **Day 09: Investigate representative unidentified matches.** Deliverable: Documented investigation.
- [x] **Day 10: Prototype roster-based team-ID recovery.** Deliverable: src/recover_team_ids.py.
- [x] **Day 11: Improve automatic roster recovery and caching.** Deliverable: Recovery script and cache.
- [x] **Day 12: Centralize OpenDota requests, retries, and caching.** Deliverable: src/opendota_client.py.
- [x] **Day 13: Refactor ingestion to use shared client.** Deliverable: Commit 1d8d743.
- [x] **Day 14: Document ingestion setup.** Deliverable: docs/INGESTION_SETUP.md; commit 9d5cb25.
- [ ] **Day 15: Inventory raw fields and define canonical match schema.** Deliverable: docs/MATCH_SCHEMA.md.
- [ ] **Day 16: Create deterministic raw-to-intermediate transform.** Deliverable: src/build_matches_int.py.
- [ ] **Day 17: Normalize timestamps and validate outcomes.** Deliverable: Intermediate transform update.
- [ ] **Day 18: Define team identity and recovered-ID provenance.** Deliverable: docs/TEAM_ID_POLICY.md.
- [ ] **Day 19: Integrate recovered IDs without overwriting raw values.** Deliverable: Intermediate transform update.
- [ ] **Day 20: Add deduplication and chronological ordering.** Deliverable: Intermediate transform update.
- [ ] **Day 21: Export intermediate matches to CSV or Parquet.** Deliverable: data/intermediate output.
- [ ] **Day 22: Document historical collection and backfill strategy.** Deliverable: docs/BACKFILL_PLAN.md.
- [ ] **Day 23: Implement historical professional-match backfill.** Deliverable: src/backfill_pro_matches.py.
- [ ] **Day 24: Add checkpoint and resume to backfill.** Deliverable: Backfill restart test.
- [ ] **Day 25: Throttle, retry and log backfill failures.** Deliverable: Hardened backfill.
- [ ] **Day 26: Backfill first bounded historical window.** Deliverable: Local raw history sample.
- [ ] **Day 27: Validate backfill coverage and match counts.** Deliverable: Coverage report.
- [ ] **Day 28: Expand bounded historical sample.** Deliverable: Additional historical data.
- [ ] **Day 29: Build tournament reference table.** Deliverable: Intermediate tournament table.
- [ ] **Day 30: Build canonical team reference table.** Deliverable: Intermediate team table.
- [ ] **Day 31: Build player and roster reference tables.** Deliverable: Intermediate roster tables.
- [ ] **Day 32: Document pre-match roster availability rules.** Deliverable: docs/ROSTER_FEATURE_RULES.md.
- [ ] **Day 33: Build chronologically ordered team match history.** Deliverable: Intermediate team history.
- [ ] **Day 34: Build prior-match rolling form features.** Deliverable: src/features/team_form.py.
- [ ] **Day 35: Build opponent-strength baseline features.** Deliverable: src/features/opponent_strength.py.
- [ ] **Day 36: Build time-decay and inactivity features.** Deliverable: src/features/recency.py.
- [ ] **Day 37: Define pre-match presentation schema.** Deliverable: docs/PRESENTATION_SCHEMA.md.
- [ ] **Day 38: Generate one row per eligible pre-match game.** Deliverable: data/presentation/prematch_games.
- [ ] **Day 39: Document feature cutoffs and leakage checks.** Deliverable: docs/LEAKAGE_CHECKLIST.md.
- [ ] **Day 40: Automate raw data quality checks.** Deliverable: tests/test_raw_quality.py.
- [ ] **Day 41: Test intermediate uniqueness and referential integrity.** Deliverable: tests/test_intermediate_quality.py.
- [ ] **Day 42: Test recovered-ID provenance and ambiguity handling.** Deliverable: tests/test_team_recovery.py.
- [ ] **Day 43: Test chronological feature calculations.** Deliverable: tests/test_feature_time_order.py.
- [ ] **Day 44: Profile missingness and tournament coverage.** Deliverable: reports/data_quality_summary.md.
- [ ] **Day 45: Define minimum training-match eligibility.** Deliverable: docs/TRAINING_ELIGIBILITY.md.
- [ ] **Day 46: Create time-based train, validation and test splits.** Deliverable: src/modeling/split_data.py.
- [ ] **Day 47: Test that no future data enters features or splits.** Deliverable: tests/test_leakage.py.
- [ ] **Day 48: Create naive and win-rate baseline predictions.** Deliverable: src/modeling/baselines.py.
- [ ] **Day 49: Create repeatable evaluation harness.** Deliverable: src/modeling/evaluate.py.
- [ ] **Day 50: Define Elo rating initialization and updates.** Deliverable: docs/ELO_SPEC.md.
- [ ] **Day 51: Implement chronological team Elo ratings.** Deliverable: src/modeling/elo.py.
- [ ] **Day 52: Generate pre-match Elo game win probabilities.** Deliverable: src/modeling/predict_elo.py.
- [ ] **Day 53: Evaluate Elo using log loss and Brier score.** Deliverable: reports/elo_evaluation.md.
- [ ] **Day 54: Tune Elo on training and validation only.** Deliverable: src/modeling/tune_elo.py.
- [ ] **Day 55: Check calibration and repeat leakage tests.** Deliverable: reports/calibration.md.
- [ ] **Day 56: Convert game probabilities to BO3 and BO5 series prices.** Deliverable: src/modeling/series_pricing.py.
- [ ] **Day 57: Normalize market odds and calculate no-vig comparisons.** Deliverable: src/pricing/market_comparison.py.
- [ ] **Day 58: Build reproducible end-to-end pipeline command.** Deliverable: src/run_pipeline.py.
- [ ] **Day 59: Publish model card, results and limitations.** Deliverable: docs/MODEL_CARD.md.
- [ ] **Day 60: Finalize README, tests, examples and v1 release.** Deliverable: v1 release notes.

## Definition of done for v1

- Repeatable pipeline from documented local raw inputs to model-ready games.
- Pre-match-only features and ratings, tested for temporal leakage.
- Out-of-sample evaluation versus a baseline with log loss and Brier score.
- BO3 and BO5 pricing with documented independence assumptions and limitations.
- Market comparison shows implied probabilities and no-vig estimates, not guaranteed arbitrage.
- Setup guide, model card, limitations, and reproducible example.

## Current status

**14/60 complete.** On the new Windows computer, OpenDota ingestion and validation ran successfully: 100 matches, 95 usable for Elo. Day 15 is next.
