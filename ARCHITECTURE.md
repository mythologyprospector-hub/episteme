# Episteme Architecture

**Status:** Canonical  
**Version:** 0.7  

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

#### Provenance Validation Policy

Phase 2 strengthens provenance validation without assigning credibility to a source.

A provenance entry is structurally valid only when:

- source_id is a non-empty string;
- captured_at is a timezone-aware ISO-8601/RFC-3339 timestamp;
- source_location, when supplied, is a non-empty absolute URI with a scheme;
- source_version, when supplied, is a non-empty string;
- note, when supplied, is a non-empty string.

Validation checks whether provenance is well-formed and inspectable. It does not determine whether the cited source is authoritative, accurate, complete, or trustworthy.

The validation boundary intentionally does not require every source to have a URL or version because scientific provenance may refer to physical, archival, local, or otherwise non-URL sources.

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

## Phase 1 Ingestion Boundary

Phase 1 provides one deliberately narrow ingestion path: UTF-8 JSON Lines containing grounded records in the canonical record shape.

The importer is a format adapter, not an epistemic authority. It parses records, applies the domain model's validation, and hands accepted records to the repository-owned store.

The importer does not:

- infer missing facts;
- repair malformed records;
- assign provenance that was not supplied;
- deduplicate records;
- promote interpretations into grounded records.

A later ingestion source may be added only when its responsibility and boundary are documented.

## Phase 2 Knowledge Integrity

Phase 2 protects the substrate from epistemic drift without changing the Phase 1 rule that grounded records require external provenance.

### Immutable Records

Grounded record content is immutable after insertion.

A correction does not overwrite the previous record. It creates a new record and an explicit lifecycle event or relationship connecting the two.

This preserves the original evidence and makes revision history inspectable.

### Lifecycle Events

Record lifecycle is represented by an append-only event log.

The initial lifecycle events are:

- created
- superseded
- retracted

A superseding event identifies the replacement record. A retraction records why the record is no longer considered active.

Lifecycle events do not rewrite the original record payload.

### Contradictions

Contradictions are represented as first-class relationships using explicit predicates such as contradicts.

A contradiction is recorded, not automatically resolved.

The existence of a contradiction does not determine which side is correct.

### Evidence Assessment

Evidence quality is represented as a contextual assessment attached to a record or relationship.

An assessment records:

- assessment method;
- assessment basis;
- rationale;
- provenance;
- assessor or process identity where available.

Evidence assessment is not a universal truth score. Different methods may produce different assessments, and the underlying evidence remains intact.

### Reproducible Transformations

A transformation records how one or more existing records produced one or more new records.

A transformation preserves:

- ordered input identifiers;
- operation name and version;
- assumptions;
- output identifiers;
- execution timestamp;
- validation result.

A transformation is itself inspectable. Its existence does not make its outputs externally true.

### Integrity Boundary

The Phase 2 integrity layer may evaluate, connect, supersede, retract, or transform records.

It may not silently rewrite grounded evidence.

The integrity layer therefore sits above the immutable grounded record substrate and below future discovery behavior.

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

## Phase 3 Discovery Architecture

Phase 3 introduces a derived discovery layer above the grounded substrate and Phase 2 integrity layer.

Discovery is analysis of represented knowledge, not a new source of knowledge.

### Discovery Findings

A discovery finding is a generated artifact that records an observed pattern in the Episteme knowledge state.

Initial finding kinds are:

- **gap** — a bounded absence or unresolved state identified relative to an explicit discovery expectation or grounded context;
- **tension** — a set of grounded inputs that cannot be cleanly reconciled under the stated discovery rule;
- **contradiction** — an explicit or reproducibly detected incompatibility between represented material;
- **unresolved_question** — a question generated from a gap or tension that identifies what remains to be learned.

Discovery findings are not grounded records and must not be inserted into the grounded `records` collection.

A finding must preserve:

- stable identifier;
- finding kind;
- human-readable title and description;
- ordered grounded input identifiers;
- discovery method and method version;
- rationale explaining why the method produced the finding;
- zero or more named significance measures;
- creation timestamp;
- schema version.

Gap findings additionally preserve the exact explicit expectation that caused the gap test to run. The expectation is structured as subject, predicate, and object; it is a discovery request, not evidence.

The input identifiers are the finding's evidential basis. The discovery method explains the transformation from those inputs to the finding.

### Discovery Traceability

A discovery result is acceptable only when its inputs can be traced to grounded or integrity-layer records.

A discovery method must never use a generated finding as independent evidence for another finding.

If a discovery process consumes generated material, that material remains explicitly generated and its upstream grounded basis must remain inspectable.

### Expectation Traceability

A gap-producing expectation must remain inspectable after discovery. The expected subject, predicate, and object are stored with the gap finding so the discovery operation does not depend on reconstructing request semantics from generated prose.

The expectation itself does not establish that the requested relationship should exist in the external world. It establishes only the question being evaluated against the represented knowledge state.

### Meaningful Gaps

Episteme does not equate graph sparsity with a scientific unknown.

A gap is meaningful only when:

1. the missing or unresolved element is bounded;
2. the expectation that makes it a gap is explicit;
3. the expectation is supplied by a grounded context or by an explicit analysis request;
4. the inputs supporting the gap are traceable;
5. the method does not treat the absence itself as proof of an external fact.

This prevents the engine from manufacturing discoveries merely because a graph is incomplete.

### Tensions and Contradictions

Contradiction discovery begins with explicit structure.

An existing relationship whose predicate is `contradicts` is a directly represented tension signal.

More sophisticated contradiction detection may compare record content later, but only when the comparison semantics are documented and reproducible. Phase 3 does not assume that two different payloads are contradictory merely because they differ.

A contradiction is surfaced, not resolved.

### Significance Measures

Significance is an attention signal, not a truth score.

Phase 3 may record multiple named measures, such as:

- evidence breadth;
- number of independent source identifiers;
- conflict density;
- coverage deficit;
- downstream dependency count.

Measures must retain their name, value, scale, and basis.

No single universal significance score is canonical in Phase 3. Different discovery methods may produce different measures, and their meanings must remain inspectable.

### Initial Discovery Methods

Phase 3 begins with deliberately narrow, reproducible methods:

1. **Explicit contradiction discovery** — surfaces grounded `contradicts` relationships.
2. **Expectation-based gap detection** — evaluates an explicit request for an expected relationship or observation against the grounded substrate.
3. **Question generation** — turns an accepted gap or tension into a bounded unresolved question without asserting an answer.
4. **Significance measurement** — derives named attention signals from the grounded inputs and discovery structure.

Semantic contradiction inference, autonomous ontology completion, model generation, and language-model-driven discovery are deferred until their epistemic boundaries are separately documented.

### Discovery Boundary

The dependency direction is:

Grounded Knowledge → Integrity → Discovery Findings

Discovery may read lower layers but must not rewrite them.

Discovery findings may become inputs to later hypothesis generation, but they remain distinguishable from grounded evidence until external evidence changes their status through an explicit process.


## Phase 4 Hypothesis and Prediction Architecture

Phase 4 adds the interpretive layer required to turn supported discovery findings into testable alternatives.

The dependency direction is:

**Grounded Knowledge → Integrity → Discovery Findings → Hypotheses / Models → Predictions**

Hypotheses and predictions are generated artifacts. They are not grounded records and do not gain epistemic authority merely because Episteme generated them.

### Hypotheses

A hypothesis is a candidate explanation that preserves:

- stable identifier;
- explanatory statement;
- ordered motivating finding identifiers;
- directly used grounded/integrity input identifiers when applicable;
- generation method and version;
- rationale;
- assumptions;
- creation timestamp;
- schema version.

Multiple hypotheses may address the same finding. The architecture must not silently select, rank, or canonize one.

### Models

Models are structured representations of explanatory mechanisms or systems. Phase 4 keeps model semantics generic rather than prematurely defining a universal scientific modeling language.

### Assumptions

Assumptions are explicit parts of explanatory proposals. Changing assumptions changes the proposal and must not silently rewrite its history.

### Predictions

A prediction is a testable consequence derived from a hypothesis or model. It preserves its source hypothesis/model, predicted consequence, conditions, assumptions, generation method, rationale, timestamp, and schema version.

A prediction is not a measurement. Independent observations or results must be explicitly related to it before any epistemic status changes.

### Distinguishing Consequences

When competing hypotheses address the same finding, Phase 4 records consequences that differ between them. These consequences become inputs to Phase 5 experiment design.

Phase 4 records what would distinguish explanations; Phase 5 determines how to obtain the discriminating observation.

The Phase 4 / Phase 5 boundary is:

**Prediction → proposed test/observation → result**

A prediction states an expected consequence under conditions and assumptions. An experiment proposal specifies a possible way to obtain an observation capable of testing that consequence. A result records what was actually observed. These are distinct epistemic objects and must not be collapsed.

### Boundary

The hypothesis layer may consume discovery findings, but it must not rewrite grounded knowledge or turn generated findings into evidence.

External reasoning systems may assist generation but remain tools. Their outputs remain generated until independently supported.


## Related Independent Research

**Tiger Den** is a separate project by the same author with a closely related epistemic posture. Tiger Den maps existing computational knowledge rather than storing or replacing the implementations themselves. Its canon emphasizes evidence before assertion, provenance, preservation of meaningful distinctions, first-class unknowns, separation of observation from interpretation, and discovery before synthesis.

The relationship is conceptual, not architectural:

- Tiger Den maps computational primitives and their existing implementations.
- Episteme provides a general scientific knowledge and discovery substrate.
- Neither project is a dependency of the other.
- Similar concepts should be compared when useful, but neither project's terminology or schema should be imported merely because the concepts sound similar.
- Cross-project observations may become useful research material only when their provenance and epistemic status are explicit.

The existence of this related project is recorded here so future builders do not independently rediscover the relationship and accidentally create an architectural dependency.
