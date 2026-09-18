# Episteme Architecture

**Status:** Canonical  
**Version:** 0.3  
**Last updated:** 2026-09-18

## Architectural Intent

Episteme is designed around one primary constraint:

> The architecture must preserve the difference between what the world provides, what the system infers, and what remains unknown.

The architecture therefore follows the epistemic model established by CANON.md.

## System Shape

At a high level:

External Evidence
      │
      ▼
┌───────────────────┐
│ Evidence Ingestion│
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Grounded Knowledge│
└─────────┬─────────┘
          ├──────────────┐
          ▼              ▼
┌───────────────────┐  ┌──────────────────┐
│ Relations / Graph │  │ Evidence Quality │
└─────────┬─────────┘  └──────────────────┘
          │
          ▼
┌───────────────────┐
│ Discovery Engine  │
└─────────┬─────────┘
          │
     ┌────┴─────┐
     ▼          ▼
Hypotheses   Unknowns / Gaps
     │          │
     └────┬─────┘
          ▼
┌───────────────────┐
│ Experiment Design │
└─────────┬─────────┘
          │
          ▼
      New Evidence

This is a conceptual architecture, not a claim that every box is currently implemented.

## Architectural Domains

### Grounded World

The grounded world contains records whose existence is attributable to an external source or reproducible observation.

Examples:

- observations
- measurements
- datasets
- papers and source documents
- experiments
- experimental results
- externally supplied metadata

Grounded records require provenance.

### Interpretive World

The interpretive world contains structures produced by reasoning over grounded material.

Examples:

- claims
- models
- hypotheses
- predictions
- analogies
- inferred relationships

Interpretive records must point back to the evidence and reasoning that produced them.

### Unknown World

The unknown world contains explicitly represented epistemic gaps.

Examples:

- unmeasured quantities
- unresolved contradictions
- insufficient evidence
- competing explanations
- unexplored relationships
- predictions that have not yet been tested

Unknowns are not automatically facts about the external world. Their provenance must explain why Episteme believes the gap exists.

## Phase 1 Knowledge Substrate

Phase 1 implements only the smallest grounded substrate needed to make the epistemic boundary executable.

### Canonical Record Shape

A grounded record has:

- a stable id;
- a kind;
- a human-readable payload;
- one or more provenance entries;
- a creation timestamp;
- a schema version.

The initial grounded kinds are:

- source
- observation
- measurement
- dataset
- experiment
- result

The record model is intentionally generic. Domain-specific fields remain inside payload until repeated use demonstrates that a field deserves a stable schema-level concept.

### Provenance

Every grounded record must have at least one provenance entry.

A provenance entry records:

- source identifier;
- source location when available;
- source version or timestamp when available;
- capture timestamp;
- optional note.

Provenance describes where the record came from. It does not certify that the external source is correct.

### Relationships

Relationships are first-class records rather than implicit dictionary links.

A relationship contains:

- stable id;
- subject id;
- predicate;
- object id;
- provenance;
- creation timestamp.

This permits relationships themselves to be evaluated, challenged, replaced, or later classified as inferred rather than grounded.

Phase 1 permits relationships between grounded records only.

### Persistence

Phase 1 uses SQLite through Python's standard library.

The persistence boundary is a repository-owned store with two logical collections:

1. records
2. relationships

Payload and provenance are stored as canonical JSON.

SQLite is an implementation choice for Phase 1, not a permanent database commitment.

### Validation

Validation occurs at the domain boundary before persistence.

A grounded record is invalid when:

- its identifier is empty or malformed;
- its kind is unsupported;
- its payload is not JSON-compatible;
- it has no provenance;
- required provenance fields are missing.

A relationship is invalid when:

- its identifier is empty or malformed;
- its subject or object does not exist;
- its predicate is empty;
- it has no provenance.

Validation failures must be explicit and must not be silently repaired.

### Identity

Identifiers are UUIDs represented as strings.

The store does not infer identity from payload similarity.

Two records with identical payloads remain distinct unless a later, explicitly documented deduplication mechanism establishes equivalence.

### Canonical Serialization

Records and relationships are serialized with deterministic JSON:

- UTF-8 text;
- sorted object keys;
- compact separators;
- no non-standard JSON extensions.

Canonical serialization makes persistence auditable and gives later provenance mechanisms a stable representation to hash or compare.

## Provenance Boundary

Every important transformation should preserve:

- source identity
- source version or timestamp where available
- input records
- transformation or reasoning step
- assumptions
- output records
- validation state

The exact transformation model remains intentionally open beyond Phase 1.

## Core Flow

The intended discovery loop is:

1. Acquire externally grounded material.
2. Normalize it without destroying provenance.
3. Represent grounded entities and relationships.
4. Evaluate evidence quality and conflicts.
5. Detect meaningful gaps, tensions, and unanswered questions.
6. Generate candidate hypotheses or models.
7. Predict consequences that could distinguish candidates.
8. Design discriminating observations or experiments.
9. Record results.
10. Update the knowledge state.
11. Repeat.

No step may silently convert an interpretation into an observation.

## Separation of Concerns

The initial architecture deliberately separates:

- evidence acquisition
- evidence representation
- provenance
- graph/relationship representation
- epistemic status
- reasoning
- discovery
- experiment design
- validation
- persistence
- interfaces

These are conceptual boundaries first. They should become software modules only when implementation justifies the boundary.

## Dependency Direction

The preferred dependency direction is toward stable epistemic primitives.

Higher-level discovery behavior may depend on evidence, provenance, relationships, and epistemic status.

Those primitives must not depend on a particular discovery strategy, language model, user interface, or external provider.

This keeps the scientific substrate independent from the mechanism used to reason over it.

## Architecture Growth Rule

New components require an explicit reason to exist.

Before adding a component, determine:

1. What responsibility cannot be cleanly handled by an existing component?
2. What invariant does the new boundary protect?
3. What data crosses the boundary?
4. What failure modes does the boundary isolate?
5. What existing documentation must change?

If those questions cannot be answered, the component is probably premature.

## Implementation Baseline

The initial executable baseline is deliberately small and boring.

- Language: Python.
- Packaging: standard pyproject.toml project metadata.
- Source layout: src/episteme/.
- Tests: tests/, using pytest.
- Dependencies: standard-library-first; external dependencies require a demonstrated need.
- Automation: GitHub Actions may verify the baseline and later project invariants.
- Interfaces: no web UI, API server, model provider, or distributed runtime is part of the baseline.

The baseline exists to make development reproducible. It is not the Phase 1 knowledge substrate.

### Python Boundary

Python is an implementation choice, not an epistemic commitment.

Core epistemic semantics must remain independent of framework-specific behavior and external service providers.

### Dependency Rule

A dependency should be introduced only when:

1. the current implementation cannot reasonably provide the required capability;
2. the dependency has a clear responsibility;
3. its role is documented;
4. its effect on reproducibility, provenance, security, and portability is understood.

## External Models

Language models and other reasoning systems are tools within Episteme, not epistemic authorities.

A model may:

- summarize
- classify
- extract
- propose relationships
- generate hypotheses
- suggest experiments
- identify possible contradictions

A model may not establish external truth by assertion alone.

## External Infrastructure

Episteme may communicate with existing system infrastructure when integration is useful.

That infrastructure is treated as an external boundary.

Episteme owns its own architecture, state, and source of truth. Integration adapters must not redefine Episteme's core semantics.

## Deferred Decisions

The following are intentionally not fixed yet:

- graph database versus relational representation beyond the Phase 1 SQLite store;
- specific ontology/schema implementation;
- language-model provider;
- web interface;
- distributed execution model;
- plugin/provider protocol;
- scientific-domain-specific schemas;
- long-term archival strategy.

These decisions will be made only when implementation requires them and will be recorded before they become architectural dependencies.

## Architectural Invariant

The most important invariant is:

> **No information may gain epistemic authority merely by passing through Episteme.**

Every later architectural decision must preserve this invariant.
