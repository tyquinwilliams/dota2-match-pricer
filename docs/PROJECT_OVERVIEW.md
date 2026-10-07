# Dota 2 Match Pricer

## Project Goal

The goal of this project is to build an open-source pricing model for professional Dota 2 matches.

The system will use historical match, team, player, and game data to estimate each team's probability of winning a match. Rather than simply predicting a winner, the model will produce a probability that can be translated into a fair market price.

The project will also serve as an open-source framework for collecting Dota 2 data, building predictive features, testing different modeling approaches, and evaluating the accuracy and calibration of match predictions.

## Problem Statement


Dota 2 is a complex team-based game where traditional match statistics may not tell the full story of which team is most likely to win. Team strength, player performance, recent form, roster composition, patches, drafting, and other factors can influence the outcome of a match.

Rather than simply predicting a winner or loser, this project aims to estimate each team's probability of winning. These probabilities can then be compared with market-implied probabilities to identify potential pricing discrepancies.

The long-term objective is to determine whether the model can consistently identify situations where the estimated probability differs meaningfully from the market price, potentially creating positive expected value.


## V1 Scope

## V1 Scope

The goal of V1 is to build a complete end-to-end data pipeline and baseline pricing model for professional Dota 2 matches.

At the end of V1, the system should be able to take two professional teams scheduled to play a match and estimate the probability of each team winning using only information that would have been available before the match.

V1 will include:

- Identification and ingestion of reliable Dota 2 data sources
- Historical professional match collection
- Team, player, hero, tournament, patch, and draft data where available
- A structured SQL data model with raw, staging, core, analytics, and feature layers
- Automated pipeline orchestration using Apache Airflow
- Data-quality checks and pipeline monitoring
- Initial feature engineering
- An Elo-based baseline pricing model
- Conversion of model output into win probabilities
- Time-based historical backtesting
- Evaluation of model accuracy and probability calibration

Market pricing, automated wagering, live-game prediction, advanced machine-learning models, and a dedicated post-draft pricing model will be considered future phases rather than requirements for V1.

## Success Criteria

## Success Criteria

V1 will be considered successful when the system can:

- Automatically collect and store historical professional Dota 2 match data.
- Maintain a structured and documented data model for matches, teams, players, heroes, patches, tournaments, and other required data.
- Run the data pipeline automatically using Apache Airflow.
- Generate historical team ratings without using information from future matches.
- Accept two professional teams as inputs and produce a pre-match win probability for each team.
- Backtest predictions against historical match results using time-based validation.
- Measure model accuracy and probability calibration.
- Reproduce the complete pipeline from documented setup instructions.

A successful V1 does not need to outperform betting markets. The primary objective is to build a reliable, reproducible pricing system that can later be expanded and tested against market prices.


## V1 System Architecture

Data will be collected from multiple Dota 2 data sources, including professional match data and recent high-MMR public match data.

A Python ingestion layer will retrieve the source data and load it into the project's data warehouse.

The warehouse will initially contain three primary layers:

Raw Layer — Stores source data as close as possible to its original form.

Intermediate Layer — Cleans, standardizes, joins, and transforms the raw data into structured datasets.

Presentation Layer — Provides analysis-ready datasets that can be used to calculate team, player, roster, tournament, and meta metrics.

Data from the presentation layer will then be used to generate model features. These features will feed the V1 Elo-based pricing model, which will generate pre-draft win probabilities for upcoming professional matches.

Apache Airflow will eventually orchestrate the ingestion, transformation, validation, feature-generation, and model processes.

The project should be designed so that it can run using an open-source/local database while maintaining the ability to support a cloud data warehouse such as Snowflake.

DOTA DATA SOURCES
        │
        ├── Professional Matches
        └── High-MMR Public Matches
                 │
                 ▼
          PYTHON INGESTION
                 │
                 ▼
             POSTGRESQL
                 │
                 ▼
               RAW
                 │
                 ▼
           INTERMEDIATE
                 │
                 ▼
          PRESENTATION
                 │
                 ▼
             FEATURES
                 │
                 ▼
          PRICING MODEL
              (Elo V1)
                 │
                 ▼
       PRE-DRAFT WIN PROBABILITY
                 │
                 ▼
       BACKTESTING / EVALUATION



### V1 Architecture Decisions

- PostgreSQL will be the primary V1 database so the project can run locally and remain free/open source.
- Python will be used for external data ingestion and model execution.
- Data will move through Raw, Intermediate, Presentation, and Feature layers.
- Apache Airflow will orchestrate the pipeline.
- Professional match data will provide historical competitive information.
- Recent high-MMR public matches will help measure the current Dota meta.
- The initial meta window will be configurable, with approximately 2–4 months as the starting range.
- Draft data will be stored when available but will not be required by the V1 pricing model.
- V1 will produce pre-draft match probabilities.
- Elo will serve as the initial baseline pricing model.
- The architecture should avoid using information that would not have been known before the predicted match.