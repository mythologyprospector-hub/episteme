# Episteme Roadmap

**Status:** Canonical planning document  
**Version:** 0.9  
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

**Status:** Complete.

## Phase 5 — Experiment Design

**Status:** Complete.

**Goal:** Find observations that efficiently discriminate among possibilities.

Target capabilities:

- [x] experiment proposals
- [x] predicted outcomes
- [x] discriminating-power analysis
- [x] explicit uncertainty/discrimination basis without a universal score
- [x] experiment/result linkage

**Exit condition:** Episteme can identify why a proposed observation would reduce uncertainty between competing explanations while preserving the distinction between prediction, proposed test, and observed result.

### Phase 5 Exit Audit

The implemented Phase 5 behavior satisfies the stated exit condition:

- experiment proposals preserve the predictions they test, their objective, proposed observation, conditions, assumptions, method/version, rationale, and explicit discrimination basis;
- the discrimination basis records why competing predictions are expected to produce different observable outcomes without becoming a universal truth or quality score;
- proposals remain generated planning artifacts and are persisted separately from grounded records;
- actual results remain grounded records with their own provenance and are not rewritten to fit a proposal;
- relationships can explicitly connect a grounded result to a generated experiment proposal and prediction without promoting either generated object to evidence;
- prediction, experiment proposal, and result remain distinct objects throughout the represented chain;
- the complete lineage is exercised by the Phase 5 result-linkage test.

The audit found no Phase 5 capability that requires new machinery before advancing. Universal statistical semantics, autonomous experiment optimization or laboratory control, instrument/provider protocols, automatic hypothesis selection, and universal uncertainty calculus remain deferred.

## Phase 6 — Closed Discovery Loop

**Goal:** Connect evidence acquisition, reasoning, experiments, and results without collapsing observation into interpretation.

Target capabilities:

- [ ] experiment result ingestion
- [ ] explicit result-to-prediction evaluation
- [ ] failed-prediction recording
- [x] explicit knowledge-state consequences
- [ ] iterative discovery
- [ ] reproducible discovery trails

**Exit condition:** A complete discovery cycle can run from grounded evidence through hypothesis, prediction, experiment, result, result evaluation, explicit knowledge-state consequence, and renewed discovery while preserving the distinction between observation and interpretation.

### Phase 6 Architecture Decision

The Phase 6 audit established that the existing result, relationship, lifecycle, evidence-assessment, and transformation primitives do not by themselves represent the semantic comparison between a result and a prediction.

Phase 6 therefore requires a distinct generated **result evaluation** concept rather than overloading evidence assessment or lifecycle events.

The evaluation is contextual and non-binary: **consistent**, **inconsistent**, or **inconclusive** under stated conditions and assumptions. It does not become evidence, does not rewrite the result or prediction, and does not constitute a universal truth or confidence score.

"Knowledge-state update" is defined as an explicit accumulation of evidence, relationships, evaluations, lifecycle events, and generated revisions. It is not a mutable universal truth flag.

The Phase 6 implementation now treats an explicit knowledge-state consequence as a separate generated artifact derived from one or more prediction evaluations. The consequence is contextual and append-only: supports, weakens, contradicts, or leaves_unresolved under stated assumptions. It does not mutate the target or establish a universal truth value.

The implementation must preserve the evaluation identifiers, target identifier, consequence classification, assumptions, rationale, method/version, timestamp, and schema version so the transition can be reconstructed.



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

**Phase 5 — Experiment Design**

Phase 1 is complete. The grounded substrate, provenance boundary, relationships, deterministic serialization, validation, SQLite persistence, and externally grounded ingestion fixture are implemented and verified.

Phase 2 is complete. The substrate now has explicit provenance validation, contradiction representation, contextual evidence assessment, immutable records, append-only lifecycle history, explicit state transitions, and reproducible transformations.

Phase 3 is complete. Discovery findings can be traced to grounded inputs, expectation-based gaps preserve their exact basis, explicit contradictions are surfaced without semantic invention, bounded questions can be generated from supported findings, interpretable measures are recorded, and generated findings remain outside the grounded evidence boundary.

Phase 4 is complete. Hypotheses, models, assumptions, competing explanations, and distinguishing predictions are represented and verified.

Phase 5 is complete. Experiment proposals explain why proposed observations could discriminate among competing explanations, actual results remain grounded and independently sourced, and explicit result-to-proposal/prediction relationships preserve the distinction between prediction, proposed test, and observed result.

Phase 6 is now the active objective: connect the represented chain into a repeatable closed discovery cycle that can ingest results, record failed predictions, update knowledge state, and preserve a reproducible discovery trail.
