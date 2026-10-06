# Bounded Exploration Scout

The bounded exploration scout is the producer side of the exploration boundary.

Its path is:

**supplied grounded records -> bounded scout -> ExplorationObservation**

The scout:

- reads only explicitly supplied record IDs;
- enforces a caller-declared maximum number of records;
- requires an explicit numeric payload field;
- records the inspected inputs, method/version, parameters, and timestamp;
- persists only a generated ExplorationObservation;
- never creates a grounded record;
- never creates a discovery finding;
- never infers a gap, candidate, relationship, or external fact.

The resulting observation can then pass through the existing durable boundary:

**ExplorationObservation -> persisted assessment -> explicit discovery finding**

## Why the scout is intentionally narrow

This first producer is a semantic proof, not a general crawler.

It demonstrates that Episteme can perform a bounded inspection and preserve its generated result without silently promoting that result to knowledge.

The scout does not choose its own inputs, access arbitrary external resources, or interpret missing positions as a discovered gap. A later explicit discovery operation may analyze the grounded inputs or the admitted generated observation.

## Contract

scout_positional_records() requires:

- explicit record IDs;
- an explicit numeric payload field;
- a positive max_records;
- a timestamp.

The returned observation preserves the exact supplied input IDs and records the represented numeric positions in deterministic order.

The observation remains generated and immutable. Its creation does not alter the grounded records.

## Non-claims

This scout does not establish:

- that a missing position exists;
- that an entity occupies a missing position;
- that a relationship exists;
- that an external source agrees;
- that the generated observation is evidence.

Those are downstream questions requiring their own explicit methods and boundaries.
