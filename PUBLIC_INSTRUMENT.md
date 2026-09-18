# Episteme Public Scientific Instrument

**Status:** Canonical Phase 8 design
**Version:** 0.1
**Last updated:** 2026-09-18

## Purpose

Phase 8 makes Episteme useful outside its development environment without turning the public interface into a second epistemic authority.

The public instrument is an interface to Episteme's existing epistemic machinery.

It must expose provenance, uncertainty, generated status, lineage, and failure rather than hiding them for convenience.

## Core Decision

Phase 8 begins with a **read-oriented scientific workspace**, not an autonomous researcher and not a broad platform.

The first public surface is a small standard-library command-line interface backed by a documented Python read API.

The first public surface should let a person:

1. inspect grounded knowledge;
2. inspect generated findings and reasoning artifacts;
3. follow provenance and lineage;
4. run deterministic discovery operations over represented knowledge;
5. inspect reproducible discovery trails;
6. export an inspectable report.

The interface does not decide what is true.

## Public API Boundary

The Python public API is read-only over an existing `Store`. It exposes inspection and trail reconstruction without introducing a second persistence model.

The initial operations are:

- inspect a grounded record by identifier;
- list grounded records in deterministic order;
- reconstruct a discovery trail;
- serialize a trail as full JSON or timestamp-independent lineage JSON;
- produce a deterministic inspection report from a discovery finding.

The CLI is an interface to these operations, not a separate application domain.

## Public Boundary

The public layer sits above the existing Episteme core:

**grounded knowledge → integrity → discovery → hypotheses/predictions → experiment proposals/results/evaluations → public interface**

The interface may request operations from lower layers, but it must not create a parallel knowledge store or reinterpret epistemic status.

## First Capability Set

Phase 8 first implementation should establish:

- a documented programmatic API for core read/query operations;
- a researcher-facing inspection surface;
- provenance and lineage navigation;
- deterministic discovery/report output;
- clear labels separating grounded records from generated artifacts;
- explicit representation of unknown, conflicting, inconclusive, and failed states.

Collaboration, review workflows, broad public ingestion, and additional domain adapters remain later capabilities unless implementation demonstrates that one is required by the first public workflow.

## Scientific Report Boundary

A reproducible discovery report is a presentation of existing Episteme state.

It is not a new epistemic object.

A report should identify:

- repository/state context;
- starting finding or requested subject;
- grounded inputs;
- generated findings and interpretations;
- hypotheses and predictions;
- experiment proposals;
- results and evaluations;
- provenance;
- reproducible lineage representation;
- generation method/version where applicable.

The report must not silently collapse generated interpretation into grounded evidence.

## Public Ingestion Boundary

Public knowledge imports remain subject to the existing grounded ingestion rules.

A public importer may adapt an external format into canonical Episteme records.

It must not:

- infer missing facts;
- repair malformed evidence silently;
- manufacture provenance;
- promote generated interpretations;
- overwrite immutable grounded records;
- silently deduplicate records by semantic similarity.

## Review Boundary

Human review is an explicit activity over represented material.

A review interface may record an assessment or other existing/generated artifact where the architecture supports it.

A reviewer action must not mutate the underlying grounded evidence merely by being performed.

## Transparency Requirements

A public-facing operation should make it possible to answer:

- What did Episteme receive?
- What did it generate?
- Which method and version produced this?
- Which grounded inputs were used?
- What remains unknown or unresolved?
- What result was actually observed?
- How was that result evaluated?
- Can the lineage be reconstructed?

Convenience must not erase these distinctions.

## Deferred

Phase 8 does not yet establish:

- autonomous scientific agency;
- automatic truth adjudication;
- a universal web-scale ingestion system;
- a universal ontology;
- a universal statistical framework;
- autonomous laboratory control;
- a mandatory frontend framework;
- a distributed deployment architecture.

Those remain separate decisions.

## Initial Exit Condition

The first Phase 8 implementation is successful when a person outside the development workflow can inspect a complete Episteme discovery cycle through a documented public interface and reconstruct why each generated step exists without losing the grounded/generated boundary.
