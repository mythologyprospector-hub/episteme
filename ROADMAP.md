# Episteme Roadmap

**Status:** Canonical planning document  
**Version:** 0.3  
**Last updated:** 2026-09-18

## Mission

Build an open scientific discovery engine that can map knowledge, expose meaningful unknowns, test competing explanations, and identify experiments that matter.

The roadmap is deliberately staged. Each stage should leave the repository more coherent than it found it.

## Phase 0 — Epistemic Foundation

**Goal:** Establish the rules before building machinery.

- [x] Establish repository.
- [x] Establish canonical principles.
- [x] Establish initial architecture.
- [x] Establish documentation standard.
- [x] Establish initial project README.
- [x] Establish contribution/change discipline.
- [x] Establish executable development baseline.

**Exit condition:** The repository has a stable vocabulary and architectural boundary sufficient to begin implementation without guessing what Episteme means by knowledge, evidence, inference, or unknown.

**Status:** Complete.

## Phase 1 — Minimal Knowledge Substrate

**Goal:** Build the smallest trustworthy representation of grounded knowledge.

Target capabilities:

- [x] source records
- [x] observations and measurements
- [x] provenance
- [x] epistemic boundary enforcement
- [x] relationships
- [x] SQLite persistence
- [x] deterministic serialization
- [x] validation
- [x] externally grounded ingestion workflow
- [x] representative end-to-end fixture

**Exit condition:** Episteme can ingest a small body of externally grounded material and represent it without collapsing evidence and interpretation.

**Status:** Complete.

## Phase 2 — Knowledge Integrity

**Goal:** Make the substrate resistant to epistemic drift.

Target capabilities:

- provenance validation
- contradiction representation
- evidence quality
- immutable or auditable history where appropriate
- explicit state transitions
- reproducible transformations

**Exit condition:** The system can explain why a represented statement exists and what evidence supports it.

## Phase 3 — Discovery

**Goal:** Find meaningful gaps and tensions in the knowledge substrate.

Target capabilities:

- gap detection
- unresolved-question generation
- contradiction discovery
- competing-model identification
- relevance and significance measures

**Exit condition:** Discovery results can be traced to grounded inputs and are distinguishable from the system's own generated material.

## Phase 4 — Hypothesis and Prediction

**Goal:** Turn discovery into testable alternatives.

Target capabilities:

- hypothesis generation
- model representation
- prediction generation
- assumption tracking
- competing explanations

**Exit condition:** Episteme can produce candidate explanations whose distinguishing consequences are explicit.

## Phase 5 — Experiment Design

**Goal:** Find observations that efficiently discriminate among possibilities.

Target capabilities:

- experiment proposals
- predicted outcomes
- discriminating-power analysis
- uncertainty tracking
- experiment/result linkage

**Exit condition:** Episteme can identify why a proposed observation would reduce uncertainty between competing explanations.

## Phase 6 — Closed Discovery Loop

**Goal:** Connect evidence acquisition, reasoning, experiments, and results.

Target capabilities:

- experiment result ingestion
- automatic knowledge-state updates
- failed-prediction recording
- iterative discovery
- reproducible discovery trails

**Exit condition:** A complete discovery cycle can run from grounded evidence through hypothesis, prediction, experiment, result, and updated knowledge.

## Phase 7 — Broadening

**Goal:** Demonstrate that the architecture survives multiple scientific domains.

Possible domains should be selected for architectural value rather than spectacle.

The system should demonstrate that domain-specific knowledge can be layered onto stable epistemic primitives without corrupting them.

## Phase 8 — Public Scientific Instrument

**Goal:** Make Episteme genuinely useful outside its development environment.

Potential capabilities:

- public knowledge imports
- researcher-facing interfaces
- reproducible discovery reports
- collaboration
- review workflows
- domain adapters
- documented APIs
- transparent evaluation

The exact public product shape remains intentionally open.

## Roadmap Rules

### No roadmap-driven architecture

A future phase does not justify building infrastructure prematurely.

Build only what the current phase requires or what a clearly demonstrated architectural invariant requires.

### No feature accumulation for its own sake

A feature belongs because it advances the mission or protects an important invariant.

### Every phase has an exit condition

A phase is complete when its stated capability is demonstrated, not merely when files exist.

### Roadmap changes are explicit

If implementation reveals that the roadmap is wrong, revise the roadmap rather than quietly drifting around it.

## Current Position

**Phase 1 — Minimal Knowledge Substrate**

The foundational documentation and executable baseline are established. The first grounded record model, provenance boundary, relationship model, deterministic serialization, validation, and SQLite persistence are implemented and verified.

The immediate objective is to prove the substrate against a small externally grounded ingestion path before adding discovery behavior.
