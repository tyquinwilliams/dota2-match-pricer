
# Dota 2 Data Source Research

## Objective

Identify reliable, low-cost data sources for the Dota 2 Match Pricer.

V1 requires:
- 12 months of professional match history
- 90 days of high-MMR public matches
- Team, player, hero, tournament, and patch data
- Individual game results and series identifiers

## Candidate 1: OpenDota

Documentation: https://docs.opendota.com/

Relevant endpoints:
- GET /proMatches
- GET /publicMatches
- GET /matches/{match_id}
- GET /proPlayers
- GET /teams/{team_id}/matches

Published free tier:
- 50,000 requests per month
- 60 requests per minute

Advantages:
- Public API documentation
- Professional and public match endpoints
- Rank filtering for public matches
- Detailed match and player statistics

Open questions:
- Historical coverage and completeness
- Series metadata quality
- Availability of parsed match details
- Ability to collect enough high-MMR matches

## Candidate 2: STRATZ

Website: https://stratz.com/

Potential alternative for detailed match data.

To verify:
- API access and authentication
- Free-tier availability and rate limits
- Professional and high-MMR coverage
- Historical data access
- Terms of use

## Candidate 3: Valve / Steam Web API

Documentation:
https://steamcommunity.com/dev

Relevant interface:
- IDOTA2Match_570/GetMatchHistory

Advantages:
- First-party match-history interface

Open questions:
- API-key requirements
- Historical coverage
- Rate limits
- Suitability for bulk ingestion

## Preliminary Recommendation

Investigate OpenDota first for the V1 ingestion prototype.

This is a provisional choice, not a final data-source decision.

## Next Steps

1. Test OpenDota's professional match endpoint.
2. Inspect returned JSON fields.
3. Check historical coverage and pagination.
4. Test high-MMR match availability.
5. Evaluate STRATZ as an alternative or supplement.
