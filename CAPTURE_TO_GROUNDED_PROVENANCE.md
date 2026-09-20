# Capture-to-Grounded Provenance Lineage

**Status:** Canonical  
**Phase:** 22  
**Boundary:** captured representation → grounded ingestion → explicit provenance lineage

## Goal

Preserve an explicit, machine-readable link from a grounded record produced by an external-source adapter to the exact captured representation that supplied its material.

## Pressure

Phases 19 and 20 established durable acquisition and capture state. Phase 21 made that state publicly inspectable. Existing grounded provenance already records source identity, capture time, source location, and source version, but those fields do not necessarily identify which acquisition event supplied a particular grounded record.

Without an explicit capture identity, Episteme can describe a source and when it was observed without being able to answer the narrower question:

> Which exact captured representation produced this grounded record?

## Invariant

> **Grounded provenance may identify the exact captured representation that supplied a record, but that operational lineage must not grant the captured material additional epistemic authority.**

The capture remains operational history. The grounded record remains grounded according to the existing provenance and ingestion rules.

## Boundary

The phase establishes this path:

**external acquisition → captured representation → source adapter → grounded record with capture-linked provenance**

The existing acquisition and capture boundaries remain authoritative for retrieval and representation preservation. The existing source adapter remains authoritative for translating a captured representation into grounded records.

## Existing Mechanism

The existing Provenance model is the correct home for this relationship.

It already travels with grounded records and already records:

- source identity;
- capture timestamp;
- source location;
- source version;
- adapter notes.

Adding an optional capture_id preserves the existing provenance mechanism rather than introducing:

- a second provenance graph;
- a new relationship predicate;
- a new transformation type;
- a reverse-index table;
- a separate lineage object.

The capture identifier points back to the durable Phase 19 capture record. The capture record remains the authoritative source for the exact content digest and immutable captured representation.

## Optionality and Compatibility

capture_id is optional.

Existing grounded records and ingestion paths that do not originate from a persisted capture remain valid and retain their existing provenance representation.

When an adapter is given a capture identifier, it must verify that the referenced capture exists before creating grounded records. This prevents a grounded record from claiming lineage to an absent acquisition event.

The existing provenance schema version remains unchanged because the new field is additive and optional; records without the field retain their prior representation.

## Crossref Vertical Proof

Phase 22 first proves the boundary through the existing Crossref adapter.

The adapter may receive capture_id alongside its existing captured timestamp and source-location inputs. Every grounded Crossref SOURCE record produced from that import receives the same capture identifier in its provenance.

The adapter does not copy capture content into provenance. The capture identifier is the explicit link; the capture record remains authoritative for content identity.

## Epistemic Boundary

Capture lineage answers an operational question:

**Which captured representation supplied this record?**

It does not answer:

**Is the captured material scientifically true?**

The presence of capture_id therefore:

- does not promote captured material to evidence by itself;
- does not validate a scientific claim;
- does not rank sources;
- does not resolve contradictions;
- does not alter generated-versus-grounded status;
- does not replace source provenance.

## Failure Behavior

A supplied capture_id that does not identify a persisted capture is rejected.

A missing capture_id remains valid for legacy or directly supplied grounded material.

No capture is created implicitly by ingestion. Acquisition and capture remain explicit upstream operations.

## Scope

### Included

- optional capture identity in grounded provenance;
- validation of capture identity;
- preservation through provenance serialization and persistence;
- Crossref adapter handoff;
- tests proving exact capture linkage and backward-compatible omission.

### Out of Scope

- new acquisition providers;
- new capture storage;
- automatic capture creation;
- capture-content duplication in grounded records;
- reverse capture-to-record indexes;
- new provenance graph structures;
- workflow execution redesign;
- public capture-lineage search;
- source ranking or evidence scoring;
- interpretation of captured material.

## Exit Condition

The phase is complete when a grounded record produced from a persisted capture can explicitly identify that capture through its existing provenance representation, the linkage survives serialization and persistence, missing capture identities are rejected, and existing provenance without capture linkage remains valid.

## Exit Audit

The implementation must demonstrate:

- exact capture identity is retained on grounded provenance;
- capture linkage survives to_dict / from_dict and Store persistence;
- missing capture identifiers are rejected before grounded records are created;
- existing provenance without capture linkage remains valid;
- Crossref remains an adapter over captured material rather than becoming an acquisition or provenance subsystem;
- no new provenance graph or reverse index is introduced;
- capture linkage does not alter epistemic status.
