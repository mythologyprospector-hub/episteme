# Episteme Architecture

**Status:** Canonical  
**Version:** 0.1  
**Last updated:** 2026-09-18

## Architectural Intent

Episteme is designed around one primary constraint:

> The architecture must preserve the difference between what the world provides, what the system infers, and what remains unknown.

The architecture therefore follows the epistemic model established in `CANON.md`.

## System Shape

At a high level:

```
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
          │
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
```

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

## Provenance Boundary

Every important transformation should preserve:

- source identity
- source version or timestamp where available
- input records
- transformation or reasoning step
- assumptions
- output records
- validation state

The exact storage model is intentionally left open until implementation establishes the smallest sufficient mechanism.

## Core Flow

The intended discovery loop is:

1. **Acquire** externally grounded material.
2. **Normalize** it without destroying provenance.
3. **Represent** grounded entities and relationships.
4. **Evaluate** evidence quality and conflicts.
5. **Detect** meaningful gaps, tensions, and unanswered questions.
6. **Generate** candidate hypotheses or models.
7. **Predict** consequences that could distinguish candidates.
8. **Design** discriminating observations or experiments.
9. **Record** results.
10. **Update** the knowledge state.
11. **Repeat**.

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

## Architecture Growth Rule

New components require an explicit reason to exist.

Before adding a component, determine:

1. What responsibility cannot be cleanly handled by an existing component?
2. What invariant does the new boundary protect?
3. What data crosses the boundary?
4. What failure modes does the boundary isolate?
5. What existing documentation must change?

If those questions cannot be answered, the component is probably premature.

## Dependency Direction

The preferred dependency direction is toward stable epistemic primitives.

Higher-level discovery behavior may depend on evidence, provenance, relationships, and epistemic status.

Those primitives must not depend on a particular discovery strategy, language model, user interface, or external provider.

This keeps the scientific substrate independent from the mechanism used to reason over it.

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

- primary database technology
- graph database versus relational representation
- specific ontology/schema implementation
- language-model provider
- web interface
- distributed execution model
- plugin/provider protocol
- scientific-domain-specific schemas

These decisions will be made only when implementation requires them and will be recorded before they become architectural dependencies.

## Architectural Invariant

The most important invariant is:

> **No information may gain epistemic authority merely by passing through Episteme.**

Every later architectural decision must preserve this invariant.
