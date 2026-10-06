# Exploration Observation Discovery Bridge

The exploration boundary is explicit and durable:

`ExplorationObservation -> persisted assessment -> discovery finding`

An `ExplorationObservation` remains a generated artifact. It is never inserted into
the grounded `records` table and its original contents are immutable.

## Assessment

`ExplorationObservationAssessment` is persisted separately and records:

- the exact observation ID;
- whether the observation was accepted for discovery;
- assessment method and version;
- rationale;
- assessment provenance;
- assessment timestamp.

A rejected assessment cannot be admitted to discovery.

## Discovery admission

An accepted observation can be explicitly admitted as a
`DiscoveryFindingKind.EXPLORATION_OBSERVATION`.

The resulting finding keeps the boundary visible:

- `input_ids` are the original grounded inputs represented by the observation;
- `context_ids` contain the generated observation and its assessment;
- the observation itself remains generated;
- no grounded record or evidence is created.

This means discovery can consume generated exploration output without silently
promoting it into canon.

## Boundary

The resulting topology is:

`grounded records -> exploration observation -> assessment -> explicit discovery context`

Any later conversion of generated material into grounded knowledge remains a
separate ingestion/admission decision and is not performed by this bridge.
