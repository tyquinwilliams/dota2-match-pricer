
# OpenDota Data Ingestion Setup

## Overview

The Dota 2 Match Pricer uses the OpenDota API to collect professional Dota 2 match data.

The ingestion pipeline is written in Python and designed to support future Elo-based match pricing.

## Project Structure

```text
dota2-match-pricer/
├── src/
│   ├── opendota_client.py
│   ├── fetch_pro_matches.py
│   ├── validate_pro_matches.py
│   └── recover_team_ids.py
├── data/
│   ├── raw/
│   │   └── pro_matches.json
│   └── cache/
│       └── opendota/
└── docs/
    └── INGESTION_SETUP.md
```

## Requirements

- Python 3.12 or compatible
- Python requests package
- Internet access for uncached API requests

## Environment Setup

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it in PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the API dependency:

```powershell
python -m pip install requests
```

## Fetch Professional Matches

Run:

```powershell
python -u src/fetch_pro_matches.py
```

The script requests professional match summaries from OpenDota and saves them to:

`data/raw/pro_matches.json`

The endpoint currently returns up to 100 recent professional matches per request.

## Validate Match Data

Run:

```powershell
python -u src/validate_pro_matches.py
```

Validation checks include:

- Duplicate match IDs
- Missing match IDs and timestamps
- Missing team IDs
- Missing match outcomes
- Matches eligible for team Elo modeling

Matches with incomplete team identification are reported separately.

## Shared API Client

`src/opendota_client.py` provides reusable API functionality.

The `get_match(match_id)` function retrieves detailed match data.

Example:

```python
from src.opendota_client import get_match

match = get_match(9040915797)
print(match["match_id"] if match else "Unavailable")
```

The client includes:

- Local JSON response caching
- Request throttling
- Automatic retries with backoff
- Graceful handling of failed requests

## API Caching

Successful responses are cached in:

`data/cache/opendota/`

Cached responses are reused on subsequent requests.

The current cache does not automatically expire. To retrieve fresh data for a cached endpoint, its cache entry must be removed or a refresh mechanism implemented.

Cache files should not be committed to Git.

## Data Quality

Some professional matches lack registered team IDs.

The project includes a roster-based recovery prototype in:

`src/recover_team_ids.py`

This identifies potential team IDs by comparing complete five-player rosters with earlier matches.

Recovered IDs are inferred candidates and must remain distinguishable from original OpenDota values.

## Current Limitations

- Ingestion currently retrieves a single page of recent professional matches.
- The cache has no automatic expiration.
- Missing team IDs can reduce Elo dataset coverage.
- Historical backfilling and database ingestion are future milestones.
