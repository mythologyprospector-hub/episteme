# Episteme Phase 16 — Public Relationship Inspection

## Goal

Expose Episteme's existing first-class relationships through the same read-only public scientific instrument already used for records, reviews, discoveries, and execution history.

## Architectural pressure

Relationships are a core grounded structure and already participate in provenance, discovery inputs, evidence assessment, and review. The store persists and deterministically lists them, but the public inspection layer does not expose the relationship objects themselves.

This leaves a gap in the public representation of the knowledge map: a researcher can inspect records and artifacts, but cannot directly inspect the explicit subject–predicate–object edges that connect represented objects.

## Governing invariant

> **Public relationship inspection may expose an asserted relationship and its provenance; it may not turn the relationship into an independently established fact.**

A relationship remains a grounded, provenance-bearing representation. Public visibility does not strengthen its evidentiary status.

## Boundary

Phase 16 extends the existing read-only path:

**persisted relationship → public Python API → CLI / HTTP transport**

No second relationship model, graph store, inference layer, or public mutation surface is introduced.

## Semantics

A relationship identifies:

- subject identifier;
- predicate;
- object identifier;
- relationship identifier;
- provenance;
- creation time;
- schema version.

The public representation reuses the existing Relationship.to_dict() representation.

Listing uses the existing deterministic store ordering. The optional predicate filter uses the store's existing predicate filter and does not invent new query semantics.

## Public surface

Python:

- get_relationship(store, relationship_id)
- list_relationships(store, predicate=None)

CLI:

- episteme --store <path> relationship <relationship_id>
- episteme --store <path> relationships [--predicate <predicate>]

HTTP:

- GET /api/v1/relationships
- GET /api/v1/relationships?predicate={predicate}
- GET /api/v1/relationships/{relationship_id}

The HTTP surface is read-only and uses the existing /api/v1 serialization and error conventions.

## Relationship to provenance and evidence

Relationship provenance remains part of the relationship representation.

Public inspection does not:

- infer facts from the edge;
- score or rank relationships;
- merge semantically similar predicates;
- calculate confidence or truth;
- mutate either endpoint;
- replace evidence assessment;
- promote generated interpretation.

A relationship can be inspected without implying that its predicate is independently verified.

## Scope

In scope:

- read-only retrieval and deterministic listing of existing relationships;
- existing predicate filtering;
- Python, CLI, and HTTP inspection;
- missing-relationship semantics;
- executable tests;
- synchronization of canonical documentation.

Out of scope:

- relationship mutation through the public instrument;
- graph databases or second relationship stores;
- inferred relationships;
- predicate ontology expansion;
- semantic similarity or deduplication;
- relationship scoring or ranking;
- automatic truth adjudication;
- reverse-index persistence;
- authentication or authorization;
- frontend infrastructure.

## Proof targets

Tests should establish:

1. persisted relationships are publicly retrievable without semantic change;
2. deterministic listing preserves existing store order;
3. predicate filtering uses the existing relationship boundary;
4. missing relationships return the existing public not-found semantics;
5. CLI inspection remains read-only;
6. HTTP inspection remains read-only and preserves existing error behavior;
7. public relationship inspection does not mutate endpoint records or relationship provenance.

## Exit condition

A researcher can directly inspect the explicit relationships that form Episteme's represented knowledge map through the same read-only public instrument, including their subject, predicate, object, provenance, and deterministic identity, without creating a second graph or changing the epistemic meaning of the relationship.

## Final principle

**A map is not fully inspectable if its edges are hidden.**
