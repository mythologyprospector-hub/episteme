# Episteme Roadmap

**Status:** Canonical planning document  
**Version:** 1.8  
**Last updated:** 2026-09-19

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

## Phase 6 — Closed Discovery Loop

**Goal:** Connect evidence acquisition, reasoning, experiments, and results without collapsing observation into interpretation.

Target capabilities:

- [x] experiment result ingestion
- [x] explicit result-to-prediction evaluation
- [x] failed-prediction recording
- [x] explicit knowledge-state consequences
- [x] iterative discovery
- [x] renewed evaluation-conflict discovery
- [x] reproducible discovery trails

**Exit condition:** A complete discovery cycle can run from grounded evidence through hypothesis, prediction, experiment, result, result evaluation, explicit knowledge-state consequence, and renewed discovery while preserving the distinction between observation and interpretation.

**Status:** Complete.

## Phase 7 — Broadening

**Goal:** Demonstrate that the architecture survives multiple scientific domains.

The canonical Phase 7 design is defined in DOMAIN_BROADENING.md.

Target capabilities:

- [x] represent two materially different scientific domains;
- [x] keep domain-specific schemas above stable epistemic primitives;
- [x] preserve provenance and core validation across domain translation;
- [x] preserve explicit missing, conflicting, and uncertain states;
- [x] preserve generated-versus-grounded boundaries;
- [x] preserve closed-loop lineage and reproducibility across domains;
- [x] demonstrate that no domain-specific workaround silently becomes a universal core rule.

**Exit condition:** Two materially different scientific domains can use domain-specific layers while preserving the same core semantics for evidence, inference, unknowns, results, evaluations, and reproducibility.

**Status:** Complete.

## Phase 8 — Public Scientific Instrument

**Goal:** Make Episteme genuinely useful outside its development environment.

The canonical Phase 8 design is defined in PUBLIC_INSTRUMENT.md.

Initial target capabilities:

- [x] read-only Python inspection API
- [x] read-only command-line inspection surface
- [x] provenance and lineage inspection
- [x] deterministic discovery report representation
- [x] researcher-facing interface beyond the CLI
- [x] public knowledge imports
- [x] collaboration and review workflows
- [x] documented external HTTP/API surface
- [x] transparent public evaluation workflow

The exact public product shape remains intentionally open.

Phase 8's currently defined public-instrument, HTTP/API, transparent-evaluation, and integrity capabilities are satisfied. Authentication, public mutation, service deployment, broader source import, and other platform concerns remain future decisions rather than prerequisites.

## Phase 9 — Structural Discovery

**Goal:** Identify meaningful holes in represented knowledge from structure, constraints, and convergent expectations rather than from arbitrary absence.

The canonical Phase 9 design is defined in STRUCTURAL_GAPS.md.

Target capabilities:

- [x] bounded positional, relational, constraint, and accounting gaps;
- [x] explicit structural context and constraint traceability;
- [x] separation of structural rules from grounded evidence and generated gaps;
- [x] inspectable structural-pressure components without a universal score;
- [x] deterministic structural-gap reproduction;
- [x] cross-domain demonstration without introducing a new domain-specific core primitive.

Candidate completion is deliberately deferred. Phase 9 establishes the hole before attempting to determine what fills it.

**Exit condition:** Episteme can identify and reproduce bounded structural gaps whose existence is established by explicit, traceable structure and constraints, while preserving the distinction between grounded evidence, structural rules, gaps, and candidate completions.

### Phase 9 Exit Audit

The implemented Phase 9 behavior satisfies the stated exit condition.

- positional gaps are bounded by an explicit numeric step and distinguish interior vacancies from boundary sparsity;
- relational gaps are established from explicit ordered structure and a declared relationship rule;
- constraint gaps require an explicit bounded region and represented neighbors around an empty interior interval;
- accounting gaps are established from an explicit total-equals-components rule and a non-zero represented residual;
- typed expectations preserve the structural form and parameters of each gap without conflating the gap with evidence;
- structural context remains inspectable through grounded input identifiers, explicit expectation data, method/version, rationale, and, where present, structural-pressure components;
- grounded evidence, structural rules, generated gaps, and candidate completions remain distinct; candidate completion remains deliberately deferred;
- structural pressure is represented as an inspectable ledger of distinct components rather than a universal pressure, confidence, coherence, importance, or truth score;
- repeated execution against the same represented state and method reproduces the same finding content apart from its intentionally fresh artifact identifier;
- accounting and bounded-constraint structures are demonstrated together as materially different structural forms without introducing a domain-specific core primitive;
- the Phase 9 structural-gap tests provide executable proof of these boundaries.

**Status:** Complete.

## Phase 10 — Candidate Completion

**Goal:** Investigate what could occupy an established structural hole without confusing candidate explanations with observations.

The canonical Phase 10 design is defined in CANDIDATE_COMPLETION.md.

Phase 10 begins only after the hole has been established. Candidate completion must preserve the gap's structural constraints, distinguish candidates from grounded evidence, expose assumptions and violations, preserve competing candidates, and identify observations that could discriminate among them.

The initial Phase 10 design is complete before implementation begins. The system must not introduce a universal plausibility, elegance, coherence, or "settlement" score as a substitute for explicit candidate fit.

**Exit condition:** Episteme can generate and assess candidate completions downstream of established structural gaps while preserving the gap, grounded evidence, constraints, assumptions, alternatives, discriminating consequences, and reproducibility.

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

**Phase 10 — Candidate Completion — Complete**

Phase 10 is complete. Candidate completion is downstream of established structural gaps; constraint assessments, competing candidates, discriminating predictions, experiment proposals, grounded results, evaluations, knowledge-state consequences, and renewed evaluation-conflict discovery are all represented without collapsing generated reasoning into evidence. The exit condition is satisfied. The next phase is intentionally not defined until a concrete architectural pressure warrants it.

Phase 1 is complete. The grounded substrate, provenance boundary, relationships, deterministic serialization, validation, SQLite persistence, and externally grounded ingestion fixture are implemented and verified.

Phase 2 is complete. The substrate now has explicit provenance validation, contradiction representation, contextual evidence assessment, immutable records, append-only lifecycle history, explicit state transitions, and reproducible transformations.

Phase 3 is complete. Discovery findings can be traced to grounded inputs, expectation-based gaps preserve their exact basis, explicit contradictions are surfaced without semantic invention, bounded questions can be generated from supported findings, interpretable measures are recorded, and generated findings remain outside the grounded evidence boundary.

Phase 4 is complete. Hypotheses, models, assumptions, competing explanations, and distinguishing predictions are represented and verified.

Phase 5 is complete. Experiment proposals explain why proposed observations could discriminate among competing explanations, actual results remain grounded and independently sourced, and explicit result-to-proposal/prediction relationships preserve the distinction between prediction, proposed test, and observed result.

Phase 6 is complete. Result records can be ingested through the grounded JSONL ingestion boundary; prediction evaluations represent result-to-prediction comparison; failed predictions are represented by inconsistent evaluations rather than mutation; explicit knowledge-state consequences are persisted; renewed discovery can surface differing evaluation outcomes while keeping generated context separate from grounded evidence; and reproducible discovery trails can reconstruct a complete cycle as an auditable lineage. The Phase 6 exit condition is satisfied.

Phase 7 is complete. Astronomy and Biology demonstrate materially different evidence shapes above the stable core, while provenance, explicit unknown/conflict/uncertainty states, generated-versus-grounded boundaries, closed-loop lineage, and reproducibility remain intact. The Phase 7 exit condition is satisfied.

Phase 8 has established its researcher-facing public instrument: a read-only Python inspection API, the installed `episteme` command, a documented external HTTP/API surface, deterministic discovery reports, a self-contained browser-readable report renderer, public knowledge import, collaboration/review inspection, and a transparent public evaluation workflow. These expose existing Episteme state rather than creating a parallel public data model. The Phase 8 initial public-instrument exit condition and the currently defined HTTP/API and transparent-evaluation capabilities are satisfied. Authentication, public mutation, broader source import, and other platform concerns remain future work rather than prerequisites. The HTTP/API integrity audit is also complete: the read-only boundary, identifier and timestamp validation, missing-resource classification, internal-error handling, and grounded/generated report separation are regression-tested and CI-verified.

Phase 9 is complete. Structural discovery can establish bounded positional, relational, constraint, and accounting holes from explicit structure and constraints; preserve typed expectations and structural context; record structural pressure as an inspectable ledger rather than a universal score; reproduce findings deterministically; and demonstrate materially different structural forms without a domain-specific core primitive. The Phase 9 exit condition is satisfied.

Phase 10 is now the active design/implementation phase. Its canonical semantics are defined in CANDIDATE_COMPLETION.md. Implementation is gated by those semantics: candidate completion must remain downstream of an established hole, preserve every inherited constraint, expose assumptions and violations, preserve alternatives, and identify discriminating consequences without collapsing fit into a universal score or turning candidates into evidence.
