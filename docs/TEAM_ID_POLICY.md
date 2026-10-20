# Team Identity and Recovery Policy

## Purpose

Define how the Dota 2 Match Pricer identifies teams consistently across historical matches without introducing future information into pre-match Elo calculations.

## 1. Identity hierarchy

Team identities have three possible sources.

### Original

The team ID was provided directly by OpenDota in the raw match record.

- Preserve the original ID.
- Set `team_id_source = original`.
- Do not overwrite the original value with an inferred ID.

### Recovered

The original team ID was missing, but a candidate identity was found using historical roster evidence.

- Store the recovered ID separately from the original raw field.
- Set `team_id_source = recovered` only after the candidate passes the recovery policy.
- Preserve the reference match ID, roster overlap, and recovery method.
- Never assume that identical player rosters always represent the same organization.

### Unresolved

Neither an original team ID nor sufficiently reliable historical evidence is available.

- Set `team_id_source = unresolved`.
- Keep the missing team identity unresolved.
- Exclude the match from team Elo calculations until the identity is resolved.

## 2. Recovery evidence

The current prototype, `src/recover_team_ids.py`, searches player match histories to identify earlier matches involving the target roster.

Its current candidate criteria are:

1. The target roster contains five identifiable players.
2. The reference match occurred strictly before the target match.
3. The reference roster contains the same five account IDs.
4. The reference match provides a team ID.
5. The candidate is returned with its supporting reference match ID.

A five-player match is treated as a candidate rather than automatically accepted as verified organizational identity.

## 3. Conflict handling

If different historical reference matches associate the same roster with different team IDs:

- Do not automatically select the first candidate.
- Mark the identity as unresolved or ambiguous.
- Retain the competing candidates for inspection.

A recovery candidate should not overwrite an existing original team ID.

## 4. Data provenance

For each recovered candidate, retain:

| Field | Description |
|---|---|
| `target_match_id` | Match with the missing team identity |
| `side` | Radiant or Dire |
| `team_id_candidate` | Proposed team ID |
| `team_name_candidate` | Historical team name |
| `reference_match_id` | Earlier match supporting the candidate |
| `matched_players` | Number of matching player account IDs |
| `history_count` | Number of player histories containing the reference match |
| `recovery_method` | Method used to generate the candidate |
| `recovery_status` | Candidate, accepted, ambiguous, or unresolved |

These are proposed recovery-output fields, not fields currently produced by the intermediate match transformation.

## 5. Temporal integrity

Only information available before a target match can be used to recover its pre-match identity.

- Reference match timestamps must be strictly earlier than the target match.
- Future roster changes cannot be used to resolve historical identities for pre-match modeling.
- Historical evidence must remain reproducible.
- Candidate retrieval limits may result in unresolved identities even when additional historical evidence exists.

## 6. Elo eligibility

A match is eligible for team Elo only when:

- Its timestamp, duration, match ID, and outcome are valid.
- Both teams have valid, distinct identities.
- Neither team's identity is ambiguous.
- Any recovered identity has passed the recovery acceptance rules.

A recovery candidate alone does not make a match eligible.

## 7. V1 implementation boundaries

Day 18 documents the identity policy.

Day 19 will address integrating optional recovered identities into the intermediate dataset without overwriting original values.

The existing recovery script is a prototype. It does not yet implement conflict detection or an automated acceptance process. Until those safeguards exist, its output should be treated as candidate evidence rather than verified identity.

Individual player Elo and more sophisticated roster-change adjustments remain outside the V1 scope.
