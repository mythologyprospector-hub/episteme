# Episteme Domain Broadening

**Status:** Canonical Phase 7 design
**Version:** 0.2
**Last updated:** 2026-09-18

## Purpose

Phase 7 tests whether Episteme's epistemic architecture remains stable when the scientific subject matter changes.

This is an architecture stress test, not a collection of domain features.

A domain demonstration is successful only when domain-specific structure can be added without changing the meaning or epistemic status of the stable Episteme primitives.

## Core Decision

Domain knowledge belongs **above** the stable epistemic substrate.

The domain layer may define:

- domain-specific record payloads;
- controlled vocabularies;
- units and measurement conventions;
- domain-specific relationships;
- domain-specific validation;
- domain-specific analysis and discovery methods.

The domain layer must not redefine:

- grounded versus generated status;
- provenance requirements;
- immutable grounded records;
- explicit generated interpretation;
- unknown/gap semantics;
- prediction/result distinction;
- evaluation semantics;
- explicit knowledge-state consequences;
- reproducibility requirements.

A domain adapter is therefore a translator and validator for domain structure, not an epistemic authority.

## Domain Boundary

The stable core remains responsible for:

1. identity;
2. epistemic status;
3. provenance;
4. persistence;
5. relationships;
6. lifecycle integrity;
7. discovery lineage;
8. generated-artifact boundaries;
9. reproducibility.

A domain layer is responsible for interpreting the meaning of its own payload fields and operations.

The core must be able to store a domain record without understanding every domain-specific field.

## What Phase 7 Must Prove

### 1. Multiple domains

At least two scientifically different domains must be represented.

The domains should differ in the structure of their evidence rather than merely in vocabulary.

### 2. Stable primitives

The same grounded record, provenance, relationship, discovery, hypothesis, prediction, proposal, result, evaluation, and trail semantics must remain usable across both domains.

### 3. Domain-specific structure stays above the core

A domain-specific schema must not require a new core epistemic primitive merely because the domain has specialized concepts.

If a genuinely new epistemic primitive is required, that is an architecture finding and must be documented before implementation.

### 4. Different evidence shapes

The demonstrations should exercise materially different evidence patterns, such as:

- scalar or tabular measurements;
- observations with categorical or structured attributes;
- time-series or repeated measurements;
- source-derived observations;
- experiments with explicit conditions.

The exact domains and evidence types are selected for architectural value.

### 5. Unknowns survive translation

A domain adapter must be able to represent:

- not measured;
- not reported;
- unresolved;
- insufficient evidence;
- conflicting observations;

without silently converting any of them into a domain-specific false, zero, null, or absence.

### 6. Provenance survives translation

Domain-specific ingestion must preserve the same provenance boundary as generic ingestion.

The adapter may add domain metadata, but it may not manufacture provenance or silently upgrade source quality.

### 7. Generated reasoning remains generated

Domain-specific discovery, hypothesis generation, prediction, experiment design, and evaluation remain generated artifacts unless independently grounded.

A domain adapter cannot promote its own interpretation merely because the interpretation uses specialized scientific vocabulary.

### 8. Reproducibility survives translation

The same domain input and method version must yield the same canonical generated structure, subject to the existing reproducibility rules.

Domain-specific transformations must expose their inputs, operation identity/version, assumptions, and outputs sufficiently for reconstruction.

## Domain Selection Rule

Do not select domains because they are impressive.

Select domains that maximize architectural pressure.

A candidate domain should be useful if it exposes one or more difficult distinctions, such as:

- measurement versus observation;
- continuous versus categorical values;
- units and dimensionality;
- repeated observations;
- experimental conditions;
- conflicting sources;
- missing measurements;
- competing explanations;
- heterogeneous provenance.

The first domain should establish the simplest clean extension point.

The second domain should deliberately stress that extension point in a different way.

## Phase 7 Domain Sequence

The first two demonstration domains are:

### Domain A — Astronomy

Astronomy is the first extension because it provides a clean pressure test for quantitative scientific observations:

- measurements with units;
- repeated observations;
- instrument/source provenance;
- observation conditions;
- missing measurements;
- source-derived and directly observed material.

The first adapter should remain deliberately small. It should demonstrate that a domain can give scientific meaning to measurement payloads without requiring the core to understand astronomical quantities.

### Domain B — Biology

Biology is the second extension because it stresses a different evidence shape:

- categorical and structured observations alongside measurements;
- experimental conditions;
- repeated trials;
- heterogeneous observations;
- conflicting observations across studies;
- explicitly unmeasured or unreported attributes.

The second adapter is intentionally not a larger copy of the first. Its purpose is to show that the extension boundary is not secretly designed around one particular kind of quantitative measurement.

The demonstrations may use small, deterministic fixtures. Their purpose is architectural verification, not scientific novelty.

## Domain Adapter Contract

A Phase 7 domain adapter should have a small, explicit boundary.

At minimum it should identify:

- domain name and version;
- domain-specific payload/schema;
- validation rules;
- translation into Episteme grounded records;
- domain-specific provenance additions, when applicable;
- any domain-specific analysis method and version.

The adapter must not:

- infer missing facts during ingestion;
- silently repair contradictory evidence;
- collapse uncertainty into defaults;
- deduplicate by semantic guesswork;
- turn generated findings into grounded records;
- mutate existing grounded records;
- bypass core validation.

## Evidence of Architectural Success

Phase 7 is not complete because two example datasets load successfully.

It is complete when the repository demonstrates that:

1. two materially different domains use the same epistemic primitives;
2. domain-specific schemas remain outside those primitives;
3. domain-specific validation cannot bypass core integrity;
4. missing and conflicting information remains explicit;
5. generated reasoning remains distinguishable from grounded evidence;
6. the closed discovery loop remains traceable;
7. reproducible lineage remains available;
8. no domain-specific workaround has silently become a universal core rule.

## Failure Is an Architectural Result

If a domain exposes a genuine limitation in the current core, the response is not to hide the limitation inside an adapter.

The sequence is:

**identify → document → determine whether the core concept is genuinely epistemic → revise canon/architecture if necessary → implement → verify**

A domain that breaks the architecture is therefore useful evidence.

## Deferred

Phase 7 does not yet establish:

- a universal ontology;
- a universal scientific units system;
- a universal domain-plugin marketplace;
- automatic schema induction;
- autonomous scientific literature interpretation;
- autonomous laboratory control;
- universal statistical semantics.

Those remain separate architectural decisions.

## Exit Condition

Phase 7 is complete when two materially different scientific domains have been represented through domain-specific layers while preserving the same core epistemic semantics, and the repository can demonstrate that the domain layer adds scientific meaning without changing the meaning of evidence, inference, unknown, result, evaluation, or reproducibility.


## Astronomy Adapter — First Implementation Boundary

The first implementation deliberately uses the existing `RecordKind.MEASUREMENT` primitive. No astronomy-specific core record kind is introduced.

The adapter lives under `src/episteme/domains/astronomy.py` and owns only astronomy-specific payload meaning.

Its canonical payload shape is:

- `domain`: `astronomy`
- `schema`: `astronomy-measurement-v1`
- `data`: domain-specific measurement fields

The initial domain fields are intentionally small:

- `quantity`: named astronomical quantity;
- `value` and `unit`: required only when status is `measured`;
- `status`: `measured`, `not_measured`, `not_reported`, or `uncertain`;
- optional `target`;
- optional `instrument`;
- optional `observed_at`;
- optional structured `conditions`.

The adapter validates structure and JSON compatibility. It does not convert units, identify celestial objects, infer missing values, judge instrument quality, or interpret scientific significance.

This creates the intended boundary:

**astronomy meaning → domain validation → ordinary Episteme measurement record → normal provenance/integrity machinery**

In particular, missing measurements remain explicit status values rather than becoming zero, null, or silently absent. Provenance is supplied by the caller and passed unchanged into the core record.

The first adapter is intentionally not an astronomy ontology or analysis engine. Its purpose is to prove that quantitative domain structure can remain above the stable epistemic substrate.


## Astronomy Uncertainty Boundary — Stress-Test Result

The first astronomy payload exposed an important boundary question: a scientific measurement can have a numeric value while the measurement itself remains uncertain. Therefore, uncertainty must not be represented by forcing the entire measurement into the `uncertain` status.

The adapter may carry domain-specific uncertainty metadata above the core measurement primitive. For the first implementation, this is represented by an optional `uncertainty` field whose structure is owned by the astronomy schema. The core stores it as ordinary payload data and does not assign statistical meaning to it.

The adapter does not establish a universal uncertainty model, confidence score, error calculus, or unit conversion system. It only validates that the optional uncertainty value is JSON-compatible and structurally representable. Domain-specific interpretation remains outside the core.

This preserves the distinction between:

- a measured value that has uncertainty;
- a quantity that was not measured;
- a quantity that was not reported;
- a result whose domain interpretation is explicitly uncertain.

No core primitive or core field is added as a result of this stress test.
