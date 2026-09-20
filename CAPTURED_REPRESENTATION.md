# Phase 19 — External Acquisition / Captured Representation

**Status:** Canonical

## Goal

Establish the smallest durable boundary for material captured from an external source before that material is translated into an Episteme grounded record.

## Pressure

Episteme can ingest and inspect grounded source records, but the system previously had no durable representation of the external material actually received during acquisition.

A URL, source identifier, or capture timestamp does not preserve the representation that was actually obtained.

## Invariant

> **A captured representation records what an external acquisition supplied; it does not gain epistemic authority merely because Episteme captured or stored it.**

The captured representation and the grounded SOURCE record derived from it remain distinct.

## Boundary

The Phase 19 boundary is:

**external source → acquisition attempt → captured representation → existing source adapter → grounded SOURCE record**

Acquisition history answers what the outside world supplied to Episteme.

Artifact provenance answers where a grounded record came from.

Workflow execution history answers what an Episteme procedure did.

These histories are complementary and must not be collapsed.

## Captured Representation

A captured representation records:

- capture identity;
- external source/provider identity;
- requested resource;
- request parameters;
- capture timestamp;
- response status when available;
- media type when available;
- source-provided version when available;
- content digest when content was captured;
- content reference when content was captured;
- acquisition method and method version;
- outcome: complete, partial, or failed;
- schema version.

The captured bytes/content are the acquired representation. Metadata describing the capture is persisted in the Episteme store.

## Storage Boundary

Phase 19 uses:

**SQLite metadata + filesystem-backed immutable content**

SQLite stores the durable description of the capture.

Captured content is stored outside SQLite under a content-addressed sha256/<digest> reference.

The physical storage mechanism is an implementation boundary, not part of the epistemic meaning of a capture.

The separation permits captured material to be backed up, copied, inspected, or exchanged independently from the Episteme database.

## Identity and Immutability

Capture identity is distinct from content identity.

Two acquisition events may capture identical content and therefore share the same content object while remaining distinct capture events.

The content digest identifies the captured representation itself.

A persisted capture identifier is append-only. Existing capture metadata cannot be overwritten.

If content already exists at its digest-derived location, a new capture may reuse it only when the bytes match the digest.

Content reads verify the digest before returning the representation.

## Failure and Partial Acquisition

A failed acquisition remains inspectable as acquisition history but does not create a grounded SOURCE record.

A partial acquisition may preserve the material actually received and must remain explicitly marked partial.

Neither failure nor partial acquisition is silently promoted to complete external evidence.

## Existing Ingestion Boundary

Phase 19 does not create a second grounded ingestion model.

A later source adapter may consume a captured representation and produce an ordinary grounded SOURCE record through the existing ingestion architecture.

The adapter remains responsible for interpreting the captured representation. Capture storage does not interpret scientific meaning.

## Scope

Phase 19 establishes:

- the captured representation model;
- durable SQLite metadata;
- filesystem-backed content storage;
- content-addressed references;
- digest verification;
- append-only capture identity;
- complete/partial/failed outcomes;
- executable persistence tests.

## Out of Scope

Phase 19 does not establish:

- automatic crawling;
- a universal web-search provider;
- provider-specific acquisition clients;
- scheduling;
- autonomous research;
- a new epistemic artifact type;
- a second ingestion system;
- automatic source ranking or quality scores;
- public mutation;
- authentication;
- distributed content storage;
- long-term archival policy;
- automatic conversion of captures into grounded records.

## Exit Condition

A captured external representation can be persisted with inspectable acquisition metadata, stored independently from SQLite as immutable content, recovered after process boundaries, verified by content digest, and represented as complete, partial, or failed without changing the epistemic status of any downstream artifact.

## Exit Audit

Phase 19 is complete when executable tests demonstrate:

- metadata and captured content survive store reopen;
- content is stored outside SQLite using the digest-derived reference;
- captured content is verified on read;
- capture identity is append-only;
- identical content may be physically reused without changing capture identity;
- failed captures remain persisted without content;
- partial captures remain explicitly partial;
- no grounded SOURCE record is created by capture storage itself.
