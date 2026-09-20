# Episteme Architecture

**Status:** Canonical  
**Version:** 1.3  

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

Beginning in Phase 5, relationships may also connect grounded records to generated epistemic artifacts such as predictions and experiment proposals. This extends the endpoint scope of the existing relationship primitive; it does not make those generated artifacts grounded.

For example, an observed result may be related to the proposal that produced the observation and to the predictions that proposal tested. The relationship remains an explicit, provenance-bearing assertion about the connection. A generated endpoint does not cause the relationship, the proposal, or the prediction to become evidence.

The relationship layer therefore distinguishes two questions:

1. **What kind of objects may be connected?** — grounded records and, from Phase 5 onward, generated epistemic artifacts.
2. **What epistemic status does the connected object have?** — preserved by the object's own model and never promoted by the relationship itself.

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



## Public HTTP/API Boundary

The external HTTP/API surface is a transport adapter over the existing read-only public API.

Its responsibility is to make existing Episteme inspection operations available to external callers without creating a second epistemic representation, persistence model, or mutation path.

The dependency direction is:

**Episteme core → read-only public API → HTTP transport**

The HTTP layer must not become a new architectural layer for evidence, discovery, interpretation, or knowledge state.

### Initial HTTP Contract

The first HTTP surface is explicitly read-only and versioned under `/api/v1`.

Initial operations expose only existing public inspection capabilities:

- retrieve one grounded record;
- list grounded records deterministically;
- retrieve one review;
- list reviews, optionally scoped by exact target kind and identifier;
- reconstruct a discovery trail;
- retrieve timestamp-independent discovery lineage;
- retrieve a discovery report;
- retrieve the same report as browser-readable HTML where supported by the public interface.

The HTTP surface must not provide mutation endpoints for records, relationships, reviews, findings, hypotheses, predictions, experiment proposals, results, evaluations, or knowledge-state consequences.

It must not expose API-key management, external provider credentials, model-provider control, crawling, autonomous ingestion, or laboratory control.

### Representation and Semantics

HTTP responses use the existing public API representations rather than defining a parallel data model.

Object-level schema versions remain part of the represented Episteme objects. The HTTP API version describes the transport contract and does not replace or reinterpret object schema versions.

The transport must preserve the distinction between:

- grounded records;
- generated artifacts;
- collaboration metadata;
- unknown or unresolved states.

An HTTP response must never promote an object merely because it was returned by the API.

JSON responses use deterministic serialization consistent with the public Python interface where deterministic output is part of the operation's contract.

### Error Semantics

The HTTP boundary must distinguish malformed requests from absent Episteme objects and operational failures.

At minimum:

- **400 Bad Request** — malformed identifiers, timestamps, filters, or query parameters;
- **404 Not Found** — the requested Episteme object or discovery target does not exist;
- **200 OK** — a valid read operation succeeded.

Operational failures must not be disguised as missing scientific knowledge.

The exact error-body schema is a transport decision and must be documented before implementation.

### Store Access

The HTTP adapter reads an Episteme store selected by server configuration.

Request handling must not mutate Episteme state.

The adapter should avoid sharing request-specific mutable state across callers. Store access and concurrency behavior are implementation concerns of the transport boundary and must not alter Episteme's epistemic semantics.

### Deployment Boundary

Authentication, TLS, reverse proxies, rate limiting, network exposure, and process supervision are deployment concerns rather than epistemic primitives.

A deployment may impose controls appropriate to its environment without changing the HTTP contract.

The initial API is therefore a public read interface, not a claim that every deployment should expose an Episteme store directly to the public internet.

### External Providers

Existing system-wide external APIs and credentials may be available to the host environment, including research, model, search, and data services.

Their existence does not make them Episteme dependencies.

When Episteme later uses an external provider, the provider belongs behind an explicit source or capability adapter. The adapter must preserve source provenance and the grounded/generated boundary. Credentials remain outside the repository and outside the epistemic data model.

This permits Episteme to operate without external providers while allowing available system capabilities to be used when a documented scientific workflow requires them.

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

**Prediction → Experiment Proposal → Result**

An experiment proposal preserves the predictions it is intended to test and describes a proposed observation or measurement. It is generated planning material, not grounded evidence.

A prediction states an expected consequence under conditions and assumptions. An experiment proposal specifies a possible way to obtain an observation capable of testing that consequence. A result records what was actually observed. These are distinct epistemic objects and must not be collapsed.

### Boundary

The hypothesis layer may consume discovery findings, but it must not rewrite grounded knowledge or turn generated findings into evidence.

External reasoning systems may assist generation but remain tools. Their outputs remain generated until independently supported.


## Phase 6 — Reproducible Discovery Trails

A reproducible discovery trail is an inspectable reconstruction of a closed-loop lineage. It is not a new epistemic object and does not become evidence.

A trail starts from a generated discovery finding and follows explicit references backward through the represented cycle:

**renewed finding → generated evaluation context → grounded result → prediction → experiment proposal when represented → hypothesis/model → motivating discovery finding → grounded/integrity inputs**

The trail must preserve object identifiers and object categories rather than copying generated prose as a substitute for identity. Each referenced object is reconstructed from the repository's canonical stored representation.

A trail has two representations. Its full serialized form includes the generation timestamp and is therefore deterministic only when the timestamp is held constant. Its reproducible lineage representation excludes that generation metadata. The lineage representation is reproducible when the same repository state, starting finding identifier, and trail-method version produce the same canonical serialized lineage. The trail records:

- starting finding identifier;
- ordered traversal entries;
- object kind and identifier for every included object;
- explicit relationship/reference used to reach each object;
- method name and version;
- generation timestamp for the trail itself;
- schema version.

The traversal is read-only. It does not create, modify, promote, supersede, or reinterpret any epistemic object.

The trail must distinguish grounded objects from generated objects throughout. Generated evaluations, consequences, findings, hypotheses, predictions, and proposals remain generated; grounded results and their provenance remain grounded.

When a reference is optional or absent, the trail records the absence rather than inventing a connection. If a required upstream object is missing, trail construction fails explicitly instead of silently repairing the lineage.

Canonical serialization of both trail representations uses the same deterministic JSON rules established for Episteme records. The full trail serialization is suitable when the generation timestamp is part of the desired record. The lineage serialization, exposed separately by the implementation, is the timestamp-independent form used for reproducibility comparison. Neither representation requires a new persistence layer.

## Phase 6 — Closed Discovery Loop

Phase 6 connects the existing epistemic objects into a repeatable cycle without collapsing grounded results into generated interpretation.

The dependency direction is:

**Grounded Knowledge → Integrity → Discovery Findings → Hypotheses / Models → Predictions → Experiment Proposals → Results → Result Evaluations / Explicit State Changes → Discovery**

### Result Ingestion

An experimental result remains a grounded result record. It is independently ingested with provenance and is never created by copying or rewriting the prediction or proposal.

Result ingestion may add explicit relationships connecting the result to the experiment proposal and the predictions it tests. These relationships describe lineage; they do not promote generated objects to evidence.

### Result Evaluation

A result does not interpret itself.

Phase 6 represents the comparison between a grounded result and a generated prediction as a distinct generated **prediction evaluation**. The evaluation is not a replacement for the result, prediction, proposal, or hypothesis, and it is not a truth score.

#### Evaluation Shape

The canonical evaluation object preserves:

- a stable identifier;
- the grounded result identifier;
- the generated prediction identifier;
- an optional experiment proposal identifier when the result was obtained through a represented proposal;
- the conditions under which this particular comparison is made;
- the assumptions used by the evaluation;
- an outcome classification;
- the rationale for that classification;
- the evaluation method and method version;
- the creation timestamp;
- the schema version.
The result and prediction identifiers are the canonical references to their descriptions. Their descriptions do not need to be copied into the evaluation because grounded records are immutable and generated prediction records are preserved as distinct artifacts. This avoids creating a second, potentially divergent textual representation while retaining reproducible access to the compared objects.

The experiment proposal identifier is optional because a result may be compared with a prediction even when no proposal is represented in the store. When present, it identifies the proposal context rather than becoming evidence.

The evaluation itself does not require provenance. Its method, method version, rationale, source object identifiers, and creation timestamp establish how the generated interpretation was produced. Any external evidence used to perform the evaluation must remain represented through the grounded result and its provenance or through separately represented inputs.

#### Outcome Classification

The initial outcome classification is deliberately non-binary:

- **consistent** — the observed result is compatible with the prediction under the stated comparison conditions;
- **inconsistent** — the observed result conflicts with the prediction under the stated comparison conditions;
- **inconclusive** — the result does not justify either classification under the available evidence and assumptions.

These classifications describe the relationship between one particular result and one particular prediction. They do not establish the truth or falsity of the underlying hypothesis.

A result may be evaluated against multiple predictions. It may be consistent with one prediction and inconsistent with another, or inconclusive for one prediction while informative about another. Each comparison is therefore represented as its own evaluation rather than forcing a single result-level verdict.

An **inconsistent** evaluation does not by itself establish that a prediction, hypothesis, or model is false. The evaluation must preserve the comparison conditions and assumptions because violated assumptions, mismatched conditions, insufficient measurement resolution, or other limitations may affect the classification.

An **inconclusive** evaluation is a valid result, not a missing evaluation. It preserves the fact that the available result did not justify either classification.

#### Persistence Semantics

Prediction evaluations are generated artifacts and therefore belong in their own persistence collection rather than the grounded `records` collection.

The initial SQLite representation is a `prediction_evaluations` table with one row per evaluation and append-only insertion semantics. Its logical fields correspond directly to the evaluation object:

- `id`;
- `result_id`;
- `prediction_id`;
- nullable `experiment_proposal_id`;
- `comparison_conditions`;
- `assumptions`;
- `outcome`;
- `rationale`;
- `method`;
- `method_version`;
- `created_at`;
- `schema_version`.

Persistence validates that:

- `result_id` identifies an existing grounded record whose kind is `result`;
- `prediction_id` identifies an existing generated prediction;
- when supplied, `experiment_proposal_id` identifies an existing generated proposal containing the evaluated prediction;
- all identifiers, text, timestamps, and schema values satisfy the domain model;
- the evaluation is inserted without modifying the result, prediction, or proposal.

No database foreign key is required for generated-object references. The repository's explicit object-existence validation remains authoritative, consistent with the existing relationship design.

### Knowledge-State Change

Phase 6 distinguishes evaluating evidence from changing represented knowledge.

A result evaluation may identify that a hypothesis or prediction is supported, weakened, contradicted, or left unresolved, but the evaluation itself does not silently rewrite the underlying artifact.

When an existing grounded record must be corrected, the existing Phase 2 lifecycle mechanism remains authoritative: create a new record and record an explicit lifecycle event such as superseded or retracted.

When a generated hypothesis, prediction, or other interpretive artifact needs revision, create a distinct generated artifact and preserve an explicit relationship to the prior artifact and the result/evaluation that motivated the revision.

This means "knowledge-state update" is not a single universal truth flag. It is the accumulation of explicit evidence, relationships, evaluations, lifecycle events, and generated revisions from which the current state can be inspected.

### Explicit Knowledge-State Consequences

Phase 6 represents a knowledge-state consequence as a distinct generated artifact when an evaluation is used to state an explicit change in how an interpretive target is regarded.

A knowledge-state consequence is not a mutable property of the target. It is an append-only record that says, in effect, "given these evaluation(s), this process derived this consequence for this target."

The initial consequence vocabulary is deliberately bounded:

- **supports** — the cited evaluation(s) provide grounds that increase support for the target under the stated conditions and assumptions;
- **weakens** — the cited evaluation(s) provide grounds that reduce support for the target under the stated conditions and assumptions;
- **contradicts** — the cited evaluation(s) provide grounds that conflict with the target under the stated conditions and assumptions;
- **leaves_unresolved** — the cited evaluation(s) do not justify a directional consequence for the target.

These are contextual generated consequences, not truth values, confidence scores, or universal rankings. In particular, **supports** does not mean true, and **contradicts** does not mean false.

A consequence must preserve:

- a stable identifier;
- one or more prediction-evaluation identifiers that motivate it;
- the target identifier;
- the consequence classification;
- the assumptions under which the consequence is stated;
- the rationale explaining the transition;
- the method and method version;
- the creation timestamp;
- the schema version.

The target may be a generated hypothesis, model, or prediction. A consequence does not mutate that target. If the target itself must change, a distinct generated artifact is created and linked to the prior artifact and the motivating consequence.

A consequence is separate from a relationship because its primary purpose is to record a generated epistemic transition with its basis and reasoning. Relationships remain the general-purpose graph connection primitive; they do not need to carry the semantics of state change.

Multiple consequences may accumulate for the same target as new evaluations arrive. Later discovery inspects that accumulation rather than reading a single mutable state field.

### Renewed Discovery Context

Phase 6 closes the loop without changing the meaning of discovery evidence.

Renewed discovery may inspect generated result evaluations and knowledge-state consequences as **derived context**. This context is not evidence and must never be placed in a discovery finding's evidential `input_ids`.

A discovery finding therefore distinguishes two kinds of lineage:

- `input_ids` — the grounded or integrity-layer objects that constitute the finding's evidential basis;
- `context_ids` — generated Phase 6 artifacts inspected by the discovery method while producing the finding.

`context_ids` may reference represented prediction evaluations and knowledge-state consequences. The repository validates that each context identifier resolves to one of those generated collections. A generated context object does not become evidence merely because discovery inspected it.

The discovery finding preserves both lists so a later reader can answer two separate questions:

1. **What evidence was this finding based on?**
2. **What generated state did the discovery method inspect?**

A renewed discovery method must preserve the same distinction in its rationale and method/version metadata. If generated context ultimately points back to grounded evidence, that upstream lineage remains available through the referenced evaluation or consequence and its underlying objects; the context identifier itself is not promoted into the evidential basis.

The first renewed-discovery method is deliberately conservative: it detects differing evaluation outcomes for the same prediction when the evaluations share the same recorded comparison conditions and assumptions.

The method:

1. groups prediction evaluations by prediction identifier, comparison conditions, and assumptions;
2. requires at least two evaluations in a group;
3. requires more than one outcome classification;
4. produces a bounded `tension` finding;
5. places the evaluated grounded result identifiers in `input_ids`;
6. places the prediction evaluation identifiers in `context_ids`.

This reports a conflict in the represented evaluation state. It does not determine which evaluation is correct, whether the prediction is true or false, or why the classifications differ.

Knowledge-state consequences are not treated as evidence. Their future use in renewed discovery requires a separate documented comparison rule.

The method is reproducible relative to the represented evaluation state and its method version. New evaluations may change what a later execution finds; earlier generated findings remain historical artifacts and are not silently rewritten.

### Failure and Uncertainty

A failed prediction is recorded as a result evaluation, not by mutating the prediction.

An inconclusive result remains inconclusive. Missing information, violated assumptions, insufficient measurement resolution, and competing interpretations must remain visible when they affect the evaluation.

Phase 6 must not introduce a universal confidence, truth, or hypothesis-ranking score merely to make the loop appear closed.

### Closed-Cycle Trace

A complete cycle is traceable when Episteme can follow:

**grounded evidence → discovery finding → hypothesis → competing prediction(s) → experiment proposal → grounded result → prediction evaluation → explicit knowledge-state consequence → renewed discovery**

The final step does not require that every result generate a new hypothesis. It requires that the resulting state remain available to the discovery layer without losing provenance or epistemic status.

## Public Evaluation Workflow

The public evaluation workflow makes an existing prediction/result comparison inspectable without creating a second truth mechanism or a public mutation API.

The workflow is:

**public evaluation packet → external execution/review → grounded result or explicit evaluation input → generated evaluation → inspectable lineage**

An evaluation packet is a deterministic, read-oriented representation of the material required to evaluate a prediction. It may include the prediction, comparison conditions, assumptions, experiment proposal where applicable, relevant grounded inputs, provenance, and the exact method/version information needed to understand the requested comparison.

The packet is a presentation of existing Episteme state, not a new epistemic object and not a claim that the included prediction is correct.

The external evaluator may be a human, script, laboratory workflow, or other process. Its execution is outside the authority of the packet. Episteme must not imply that an evaluator actually performed an observation merely because a packet was exported or viewed.

When an observation is actually made, the observation or result enters Episteme through the ordinary grounded-ingestion boundary with its own provenance. When a result is compared with a prediction, the comparison is represented by the existing PredictionEvaluation primitive, preserving result, prediction, conditions, assumptions, outcome, rationale, and method/version.

The initial public workflow is deliberately asymmetric:

- Episteme exposes what should be evaluated and why;
- an external evaluator performs or reports the work;
- grounded results retain independent provenance;
- evaluation remains generated interpretation;
- the public read surface exposes the complete chain afterward.

The workflow must not accept a public assertion as a grounded result without provenance, turn evaluator identity into scientific authority, collapse evaluation outcomes into a truth score, silently mutate predictions or hypotheses, hide assumptions or method versions, or require a network service or model provider.

This boundary permits transparent public evaluation while preserving the existing read-only HTTP contract and the distinction between observation and interpretation.

### Evaluation Packet Invariants

A packet must make it possible to answer:

- what prediction is being evaluated;
- what conditions and assumptions apply;
- what proposed observation or measurement would discriminate the alternatives;
- which existing grounded material provides context;
- which method and version define the requested evaluation;
- what Episteme expects an external evaluator to return.

A packet must not imply that an unperformed experiment has produced a result.

### Evaluation Completion

Completion is represented by existing Episteme objects rather than a new public truth state:

1. external work produces a grounded result with provenance;
2. the result is linked to the relevant proposal/prediction where appropriate;
3. a generated PredictionEvaluation compares the result and prediction under explicit conditions and assumptions;
4. any KnowledgeStateConsequence is recorded separately when a process explicitly derives one;
5. renewed discovery may inspect the resulting generated state without treating it as evidence.

## Collaboration and Review Layer

Human review is an explicit layer over represented Episteme material. It is orthogonal to the grounded/generated/unknown epistemic layers: recording a review does not change the epistemic status of its target.

A review identifies exactly one persisted target by both target kind and target identifier and preserves:

- reviewer identity;
- explicit disposition;
- review basis;
- rationale;
- reviewer/process provenance;
- review timestamp;
- schema version.

The initial disposition vocabulary is deliberately non-authoritative:

- **note** — records an observation or comment about the target;
- **question** — records something the reviewer asks or seeks clarification about;
- **challenge** — records a reason to question the target or its reasoning;
- **acknowledge** — records that the reviewer examined the target without asserting a truth judgment.

These dispositions are review actions, not truth values, confidence scores, consensus states, or rankings.

Reviews are immutable and append-only. A review never overwrites, retracts, supersedes, or reclassifies its target. Multiple reviews may target the same object, including reviews with different dispositions or conclusions; disagreement remains inspectable rather than being collapsed into consensus.

The target boundary initially includes grounded records, relationships, discovery findings, hypotheses, models, predictions, experiment proposals, prediction evaluations, and knowledge-state consequences. A review target must already exist when the review is persisted. The target kind is part of the identity of the reference so inspection cannot accidentally conflate objects from different persistence collections.

Reviewer identity is intentionally a free-form field in the initial implementation, supplemented by provenance. Accounts, authentication, permissions, shared editing, threaded discussion, notifications, workflow automation, and consensus computation remain outside this layer.

### Review Versus Evidence Assessment

Evidence assessment and review serve different purposes. Evidence assessment evaluates a grounded record or relationship under a stated assessment method and basis. Review records examination of represented material, including generated artifacts. A review may discuss or reference an assessment, but it does not replace the assessment and does not promote generated material to evidence.

### Persistence Boundary

Reviews are stored separately from the objects they examine. Persistence validates the target reference before insertion and uses append-only insertion semantics. The reviewed object remains unchanged. Duplicate review identifiers are rejected by normal store uniqueness constraints rather than overwriting an existing review.

Review records are collaboration metadata, not discovery-trail nodes. They may be inspected alongside their targets, but they do not become evidential inputs merely because a reviewer examined an object.


## Phase 9 Structural Discovery

Phase 9 introduces structural-gap discovery as a distinct discovery capability. The architectural boundary is deliberately two-stage: first establish a bounded hole from represented structure and explicit constraints; only later attempt candidate completion.

Structural discovery may use relationships, ordered grounded fields, constraints, and accounting structures. Its findings preserve grounded inputs separately from generated structural expectations and generated context.

Discovery expectations are typed rather than relationship-shaped. The initial kinds are relationship, positional, constraint, and accounting. This allows later constraint and accounting gaps to be represented without pretending that every unknown is a missing graph edge.

The expectation is not evidence and is not a universal fit, coherence, importance, or truth score. Its method and structured data must make the structural rule inspectable and reproducible. Legacy relationship-shaped persisted expectations remain readable during this transition.

Structural pressure is represented as an immutable ledger of typed components attached to a gap finding. Each component preserves its structural basis, grounded input identifiers, and method/version. The ledger is deliberately not a scalar score and does not infer statistical independence merely by counting components.

## Phase 15 Artifact-to-Execution Lineage

Phase 15 establishes the reverse inspection path from an existing artifact to persisted workflow executions that consumed or produced it. The relationship is derived from Phase 13 `WorkflowStepResult.input_ids` and `output_ids`; it is not persisted as a second graph or provenance model.

The canonical traversal is:

**artifact → execution(s) → step(s) → input/output artifact identifiers**

The public lookup reuses the existing `WorkflowExecution` representation and deterministic execution ordering. An execution appears at most once for a given artifact even when that artifact occurs in multiple steps.

Artifact-to-execution linkage is computational history, not provenance, evidence, confidence, validation, or truth. Existing artifact provenance remains independent and unchanged. An artifact can have provenance without workflow history, and workflow history does not confer epistemic authority.

The public boundary is read-only through the Python API, CLI, and `/api/v1/artifacts/{artifact_id}/executions`. Missing artifacts are distinguished from known artifacts with no matching execution history.

No persisted reverse index is required at this stage. The lookup scans the existing persisted execution history, keeping Phase 13 as the sole execution persistence boundary.

## Related Independent Research

**Tiger Den** is a separate project by the same author with a closely related epistemic posture. Tiger Den maps existing computational knowledge rather than storing or replacing the implementations themselves. Its canon emphasizes evidence before assertion, provenance, preservation of meaningful distinctions, first-class unknowns, separation of observation from interpretation, and discovery before synthesis.

The relationship is conceptual, not architectural:

- Tiger Den maps computational primitives and their existing implementations.
- Episteme provides a general scientific knowledge and discovery substrate.
- Neither project is a dependency of the other.
- Similar concepts should be compared when useful, but neither project's terminology or schema should be imported merely because the concepts sound similar.
- Cross-project observations may become useful research material only when their provenance and epistemic status are explicit.

The existence of this related project is recorded here so future builders do not independently rediscover the relationship and accidentally create an architectural dependency.

## Phase 16 — Public Relationship Inspection

Public relationship inspection extends the read-only public instrument to expose the existing first-class subject–predicate–object relationships and their provenance. It reads the existing relationship persistence boundary; it does not create a second graph, infer new edges, score relationships, or add public mutation. The public boundary is persisted relationship → Python inspection API → CLI/HTTP. Relationship visibility does not upgrade the epistemic status of the represented relationship.


## Phase 17 — Public Epistemic Artifact Inspection

Phase 17 extends the existing read-only public instrument to expose the persisted generated epistemic artifacts already used by the discovery loop: hypotheses, models, predictions, experiment proposals, prediction evaluations, and knowledge-state consequences. The boundary is persisted generated artifact → public Python API → CLI/HTTP. Existing model serialization and Store persistence remain authoritative. Public visibility does not promote generated artifacts to grounded evidence, and no second artifact model, inference layer, score, or mutation surface is introduced.


## Phase 18 — Public Discovery Finding Inspection

Phase 18 extends the existing read-only public scientific instrument to expose persisted `DiscoveryFinding` objects directly. The boundary is:

**persisted DiscoveryFinding → public Python API → CLI/HTTP**

The public surface reuses the existing `DiscoveryFinding` model, Store persistence, serialization, and generated status. It provides direct retrieval plus deterministic listing with the existing finding-kind filter.

This closes the inspection gap between discovery trails or downstream generated artifacts and the discovery finding itself. It does not add discovery semantics.

The public dependency direction remains:

**Discovery Findings → read-only public API → CLI/HTTP**

Public inspection must not:

- create or mutate findings;
- infer new findings;
- rank or score findings;
- create a second finding representation or provenance graph;
- promote a finding to grounded evidence.

A discovery finding remains generated material regardless of whether it is inspected directly, listed, or referenced by another public surface.

The canonical Phase 18 public contract is defined in `PUBLIC_DISCOVERY_FINDING_INSPECTION.md`.
