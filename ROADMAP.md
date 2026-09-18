# Episteme Roadmap

**Status:** Canonical planning document  
**Version:** 0.7  
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

- [x] provenance validation beyond Phase 1 structural checks
- [x] contradiction representation
- [x] contextual evidence assessment
- [x] immutable record content and append-only lifecycle history
- [x] explicit state transitions
- [x] reproducible transformation records

**Exit condition:** The system can explain why a represented statement exists and what evidence supports it.

**Status:** Complete.

## Phase 3 — Discovery

**Goal:** Find meaningful gaps and explicit contradictions in the knowledge substrate.

Target capabilities:

- [x] gap detection with explicit expectation traceability
- [x] unresolved-question generation
- [x] explicit contradiction discovery
- [x] interpretable significance measures

The following remain deliberately deferred from Phase 3 because their epistemic rules are not yet sufficiently defined:

- semantic tension detection;
- competing-model identification;
- universal relevance or importance scoring.

**Exit condition:** Discovery results can be traced to grounded inputs, meaningful gaps and explicit contradictions can be surfaced, bounded unresolved questions can be generated, interpretable measures can be recorded, and all generated material remains distinguishable from the system's own grounded evidence.

**Status:** Complete.

### Phase 3 Exit Audit

The implemented Phase 3 behavior satisfies the stated exit condition:

- grounded records and relationships are inspected directly by discovery methods;
- gap findings preserve the exact expected subject, predicate, and object;
- explicit `contradicts` relationships are surfaced without inventing semantic contradiction;
- unresolved questions are generated only from gaps or tensions and preserve their source finding;
- discovery methods record a method name and version, grounded input identifiers, rationale, and creation time;
- named measures record their scale and basis, including input count and source diversity;
- discovery findings are persisted separately from grounded records, and generated findings cannot be supplied as independent evidence inputs.

The audit found no Phase 3 capability that requires new machinery before advancing. Semantic tension detection, competing-model identification, universal importance scoring, and automatic finding-to-hypothesis conversion remain deferred as documented in DISCOVERY.md.


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

**Phase 3 — Discovery**

Phase 1 is complete. The grounded substrate, provenance boundary, relationships, deterministic serialization, validation, SQLite persistence, and externally grounded ingestion fixture are implemented and verified.

Phase 2 is complete. The substrate now has explicit provenance validation, contradiction representation, contextual evidence assessment, immutable records, append-only lifecycle history, explicit state transitions, and reproducible transformations.

Phase 3 is now the active objective: detect meaningful gaps and tensions without confusing generated structure with externally grounded evidence. Phase 3 architecture is deliberately narrow: discovery findings remain derived artifacts, explicit contradictions are surfaced before semantic contradiction inference, and gaps require an explicit expectation or grounded context.
