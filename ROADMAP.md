# Episteme Roadmap

**Status:** Canonical planning document  
**Version:** 2.0  
**Last updated:** 2026-09-20

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

**Status:** Complete.

## Phase 11 — Grounded Evidence Ingestion

**Goal:** Strengthen the boundary through which heterogeneous, finite external scientific material enters Episteme without weakening provenance or the grounded/generated distinction.

The canonical Phase 11 design is defined in GROUNDED_INGESTION.md.

Target capabilities:

- [x] accept at least two materially different finite external source representations;
- [x] preserve source identity, source state, and capture provenance;
- [x] preserve source-provided content without silently changing its epistemic meaning;
- [x] translate deterministically under a named adapter and version;
- [x] use existing transformation semantics when translation lineage is materially important;
- [x] explicitly reject malformed or unsupported material;
- [x] preserve immutable records across re-import;
- [x] keep generated interpretation outside the grounded evidence boundary;
- [x] provide executable tests for heterogeneous ingestion and provenance/translation lineage.

**Exit condition:** Episteme can ingest heterogeneous finite source representations while preserving source provenance, translation lineage, deterministic behavior, immutable records, and the distinction between externally grounded material and generated interpretation.

**Status:** Complete.

### Phase 11 Exit Audit

The implemented Phase 11 behavior satisfies the stated exit condition.

- canonical JSONL and nested Crossref work-metadata representations provide materially different finite source forms;
- source identity, source location, source version/state, capture timestamps, and source-provided content are preserved where represented;
- the Crossref adapter is explicitly named and versioned, with deterministic record identity and payload behavior;
- existing Transformation semantics preserve material translation lineage without introducing a second ingestion model;
- malformed source material is rejected before persistence, including whole-batch validation boundaries;
- immutable records cannot be overwritten by re-import;
- source metadata remains a grounded SOURCE record and does not manufacture hypotheses, predictions, or discovery findings;
- executable tests cover heterogeneous ingestion, provenance, deterministic adapter behavior, rejection, immutability, and translation lineage.

**Status:** Complete.

## Phase 12 — Discovery Orchestration

**Goal:** Make the existing discovery machinery executable as a declared, reproducible, inspectable workflow without introducing a new epistemic authority or second knowledge model.

The canonical Phase 12 design is defined in DISCOVERY_ORCHESTRATION.md.

Target capabilities:

- [x] declared finite workflow representation;
- [x] composition of existing epistemic primitives;
- [x] ordered execution lineage;
- [x] grounded/generated boundary preserved across workflow steps;
- [x] competing alternatives preserved;
- [x] explicit failure states without erasure;
- [x] reproducibility relative to declared state, parameters, assumptions, and method versions;
- [x] post-execution workflow inspection;
- [x] executable end-to-end workflow proof.

**Exit condition:** Episteme can execute and inspect a finite declared discovery workflow composed from existing primitives while preserving epistemic boundaries, alternatives, failures, and reproducibility.

**Status:** Complete.

## Phase 13 — Execution History

**Goal:** Preserve durable, inspectable history of finite discovery workflow executions without turning execution metadata into epistemic authority.

The canonical Phase 13 design is defined in EXECUTION_HISTORY.md.

Target capabilities:

- [x] persist declared workflow definitions without semantic drift;
- [x] persist workflow execution occurrences and ordered step lineage;
- [x] preserve actual effective inputs, outputs, method versions, and failures across process boundaries;
- [x] preserve immutable historical execution identity;
- [x] preserve timestamp-independent reproducibility semantics;
- [x] preserve grounded/generated boundaries and existing artifact provenance;
- [x] provide read-only inspection of persisted execution history where justified.

**Exit condition:** A finite declared workflow can be executed, persisted, recovered, and inspected after the original process has ended, with complete step lineage, method/version history, failure history, reproducibility semantics, and unchanged epistemic boundaries.

**Status:** Complete.

### Phase 13 Exit Audit

The implemented Phase 13 behavior satisfies the stated exit condition.

- workflow definitions persist and recover without semantic drift, including absent optional parameters;
- workflow executions persist and recover across process boundaries;
- actual effective step inputs and produced outputs are preserved, including downstream propagation;
- step and workflow method/version history survives persistence and failure;
- failed executions retain completed prior steps and the exact failure boundary;
- duplicate workflow definitions and executions are rejected, preserving append-only historical identity;
- repeated executions receive distinct identities while equal declared executions retain equal timestamp-independent lineage;
- persisted execution history does not alter grounded/generated artifact classification;
- artifact-level provenance remains separate and independently valid;
- executable Phase 13 tests provide proof of the durable boundary.

**Status:** Complete.

## Phase 14 — Public Execution Traceability

**Goal:** Expose the durable execution history established by Phase 13 through Episteme's existing public scientific instrument without turning execution metadata into epistemic authority.

The canonical Phase 14 design is defined in PUBLIC_EXECUTION_TRACEABILITY.md.

Target capabilities:

- [x] read-only public retrieval of persisted workflow definitions;
- [x] read-only public retrieval of persisted workflow executions;
- [x] deterministic listing of persisted workflow definitions and executions where justified;
- [x] timestamp-independent execution lineage inspection;
- [x] read-only CLI execution-history inspection;
- [x] versioned HTTP read routes using the existing public representation;
- [x] preservation of workflow-definition, workflow-execution, and epistemic-artifact distinctions;
- [x] executable tests covering the public execution boundary.

**Exit condition:** A researcher using Episteme's documented public inspection surfaces can inspect a persisted workflow definition and execution, reconstruct its ordered computational history and success/failure boundary, compare timestamp-independent lineage, and inspect the relationship to existing Episteme artifacts without execution metadata acquiring epistemic authority.

**Status:** Complete.

### Phase 14 Exit Audit

The implemented Phase 14 behavior satisfies the stated exit condition.

- persisted workflow definitions are exposed through the existing read-only public API without semantic reinterpretation;
- persisted workflow executions are exposed through the same public boundary without creating a parallel execution representation;
- workflow and execution listings use the existing deterministic store ordering;
- timestamp-independent execution lineage is publicly inspectable without execution identity or timestamps entering the lineage representation;
- failed executions remain publicly inspectable with completed prior steps, the failure boundary, effective inputs, and failure information preserved;
- CLI execution-history commands use the read-only store path and introduce no mutation surface;
- versioned HTTP routes expose workflow definitions, executions, and execution lineage through /api/v1 while preserving existing read-only error and mutation semantics;
- workflow definitions, workflow executions, and epistemic artifacts remain distinct, and execution metadata does not alter grounded/generated classification or artifact provenance;
- the public execution surface reads the Phase 13 persistence boundary rather than creating a second persistence or epistemic model;
- executable Phase 14 tests provide proof of the public execution boundary, and the resulting GitHub Actions Test run for commit 91261f127b2b3303910f8e5dbcd16928f3d53bbd completed successfully.

**Status:** Complete.

## Phase 15 — Artifact-to-Execution Lineage

**Goal:** Make the relationship between existing Episteme artifacts and the persisted workflow executions that consumed or produced them directly inspectable without creating a second provenance or execution model.

The canonical Phase 15 design is defined in ARTIFACT_EXECUTION_LINEAGE.md.

Target capabilities:

- [x] reverse lookup from an existing artifact to persisted workflow executions;
- [x] matching against both step inputs and outputs;
- [x] deterministic execution ordering and per-execution deduplication;
- [x] explicit missing-artifact semantics;
- [x] read-only Python, CLI, and /api/v1 HTTP inspection;
- [x] preservation of artifact provenance and execution semantics;
- [x] executable tests covering the reverse execution boundary.

**Exit condition:** A researcher can start from an existing Episteme artifact and inspect every persisted workflow execution that consumed or produced it, including the relevant step-level input/output history, through the same read-only public instrument used for Phase 14, without changing artifact meaning, provenance, or execution semantics.

**Status:** Complete.

### Phase 15 Exit Audit

The implemented Phase 15 behavior satisfies the stated exit condition.

- artifact-to-execution lookup derives exclusively from persisted workflow step input/output identifiers;
- one execution is returned at most once even when an artifact occurs in multiple steps;
- results preserve the existing deterministic execution ordering;
- missing artifact identifiers are rejected rather than presented as known artifacts with empty history;
- the Python API, CLI, and /api/v1 HTTP route are read-only;
- no reverse-index persistence table or second artifact/execution model was introduced;
- artifact provenance and grounded/generated semantics remain unchanged;
- executable Phase 15 tests cover input/output matching, deduplication, missing-resource behavior, CLI inspection, and HTTP inspection.

**Status:** Complete.


## Phase 16 — Public Relationship Inspection

**Goal:** Expose the existing first-class subject–predicate–object relationships through the read-only public scientific instrument without changing their epistemic meaning.

The canonical Phase 16 design is defined in PUBLIC_RELATIONSHIP_INSPECTION.md.

Target capabilities:

- [x] read-only public retrieval of persisted relationships;
- [x] deterministic relationship listing with the existing predicate filter;
- [x] read-only CLI relationship inspection;
- [x] versioned HTTP relationship inspection;
- [x] preservation of relationship provenance and grounded/generated boundaries;
- [x] executable tests covering the public relationship boundary.

**Exit condition:** A researcher can directly inspect persisted first-class relationships and their provenance through the existing read-only public instrument without creating a second graph or changing relationship meaning.

**Status:** Complete.

## Phase 17 — Public Epistemic Artifact Inspection

**Goal:** Expose existing generated epistemic artifacts through the existing read-only public scientific instrument without changing their epistemic status.

The canonical Phase 17 design is defined in PUBLIC_EPISTEMIC_ARTIFACT_INSPECTION.md.

Target capabilities:

- [x] read-only public retrieval and listing of hypotheses;
- [x] read-only public retrieval and listing of models;
- [x] read-only public retrieval and listing of predictions;
- [x] read-only public retrieval and listing of experiment proposals;
- [x] read-only public retrieval and listing of prediction evaluations;
- [x] read-only public retrieval and listing of knowledge-state consequences;
- [x] read-only CLI inspection for each artifact type;
- [x] versioned HTTP read routes for each artifact type;
- [x] preservation of generated-versus-grounded boundaries;
- [x] executable tests covering the public artifact boundary.

**Exit condition:** A researcher using Episteme's documented public inspection surfaces can directly retrieve and list each existing generated epistemic artifact type, inspect its stored content and lineage fields, and distinguish it from grounded evidence without creating a second artifact model or changing its epistemic status.

**Status:** Complete.

## Phase 18 — Public Discovery Finding Inspection

**Goal:** Expose existing generated discovery findings through the existing read-only public scientific instrument without changing their epistemic status.

The canonical Phase 18 design is defined in PUBLIC_DISCOVERY_FINDING_INSPECTION.md.

Target capabilities:

- [x] read-only public retrieval of persisted discovery findings;
- [x] deterministic listing of discovery findings;
- [x] existing discovery-finding kind filter;
- [x] read-only CLI inspection;
- [x] versioned HTTP read routes;
- [x] preservation of generated-versus-grounded boundaries;
- [x] executable tests covering the public discovery-finding boundary.

**Exit condition:** A researcher can directly inspect a persisted discovery finding and deterministically list existing findings through Episteme's public Python, CLI, and HTTP surfaces, while the finding remains explicitly generated and retains its existing content and provenance relationships.

**Status:** Complete.

## Phase 19 — External Acquisition / Captured Representation

**Goal:** Preserve the external material actually received by Episteme as an immutable, inspectable capture without conflating acquisition history with grounded evidence, artifact provenance, or workflow execution history.

The canonical Phase 19 design is defined in CAPTURED_REPRESENTATION.md.

Target capabilities:

- [x] captured representation model;
- [x] durable SQLite capture metadata;
- [x] filesystem-backed immutable content;
- [x] content-addressed SHA-256 references;
- [x] digest verification on write and read;
- [x] append-only capture identity;
- [x] complete, partial, and failed acquisition outcomes;
- [x] executable persistence tests.

**Exit condition:** A captured external representation can be persisted with inspectable acquisition metadata, stored independently from SQLite as immutable content, recovered after process boundaries, verified by content digest, and represented as complete, partial, or failed without changing the epistemic status of downstream artifacts.

**Status:** Complete.

## Phase 20 — External Acquisition

**Goal:** Perform bounded external retrieval through an explicit provider boundary and hand the exact received representation into the existing Phase 19 capture boundary without changing epistemic status.

The canonical Phase 20 design is defined in EXTERNAL_ACQUISITION.md.

Target capabilities:

- [x] provider-neutral acquisition request and response contract;
- [x] explicit complete, partial, and failed acquisition outcomes;
- [x] durable handoff into Phase 19 captured representation;
- [x] bounded Crossref acquisition provider;
- [x] exact response preservation and content-digest verification;
- [x] explicit failure descriptions;
- [x] preservation of distinct acquisition events for identical content;
- [x] executable tests covering success, failure, partial, provider-boundary, adapter handoff, and repeat-acquisition behavior.

**Exit condition:** A bounded external request can be performed through an explicit provider capability, with the request and outcome inspectably represented, the exact received representation handed to Phase 19 immutable capture, and the captured representation optionally passed through the existing Crossref adapter into grounded ingestion without acquisition itself changing epistemic status.

### Phase 20 Exit Audit

The implemented Phase 20 behavior satisfies the stated exit condition.

- bounded provider requests produce persisted captured representations;
- request/resource and acquisition method metadata survive persistence;
- successful response content is preserved exactly and verified by the Phase 19 digest boundary;
- failed acquisition remains distinguishable from successful capture and preserves an explicit failure description;
- partial acquisition preserves received content while remaining explicitly partial;
- provider-specific Crossref behavior remains outside the stable capture and epistemic primitives;
- acquisition does not itself create grounded records;
- captured Crossref responses flow through the existing adapter and grounded ingestion boundary;
- repeated acquisition events remain distinct even when captured content is identical;
- executable Phase 20 tests provide proof of these boundaries.

**Status:** Complete.

## Phase 21 — Public Acquisition / Capture Inspection

**Goal:** Expose persisted external acquisition and captured-representation state through the existing read-only public scientific instrument without changing its epistemic status.

The canonical Phase 21 design is defined in PUBLIC_ACQUISITION_CAPTURE_INSPECTION.md.

Target capabilities:
- [x] read-only public retrieval of persisted captured representations;
- [x] deterministic listing of captured representations;
- [x] source-identifier filtering;
- [x] read-only CLI inspection;
- [x] versioned HTTP read routes;
- [x] preservation of existing capture representation and epistemic boundaries;
- [x] executable tests covering the public acquisition/capture boundary.

**Exit condition:** A researcher can directly retrieve a persisted captured representation and deterministically list captures through Episteme's public Python, CLI, and HTTP surfaces, including source filtering, while preserving the existing capture representation and epistemic boundary.

**Status:** Complete.

## Phase 22 — Capture-to-Grounded Provenance Lineage

**Goal:** Preserve an explicit link from grounded records produced by external-source adapters to the exact persisted capture that supplied their material, using the existing provenance mechanism without changing epistemic status.

The canonical Phase 22 design is defined in CAPTURE_TO_GROUNDED_PROVENANCE.md.

Target capabilities:

- [x] optional capture identity in grounded provenance;
- [x] validation of referenced capture identity;
- [x] preservation through provenance serialization and Store persistence;
- [x] Crossref adapter handoff;
- [x] backward-compatible provenance without capture linkage;
- [x] executable tests covering exact lineage and missing-capture rejection;
- [x] content-bound Crossref handoff that rejects supplied data differing from the persisted capture.

**Exit condition:** A grounded record produced from a persisted capture can explicitly identify that capture through its existing provenance representation, the adapter verifies that supplied Crossref data matches the persisted captured representation before producing grounded records, the linkage survives serialization and persistence, missing or mismatched captures are rejected, and existing provenance without capture linkage remains valid.

**Status:** Complete.


## Phase 23 — Public Captured Content Inspection

**Goal:** Expose the exact immutable captured representation through Episteme's existing read-only public scientific instrument without changing its epistemic status.

The canonical Phase 23 design is defined in PUBLIC_CAPTURED_CONTENT_INSPECTION.md.

Target capabilities:

- [x] exact raw captured-content inspection;
- [x] explicit capture-root configuration for public content access;
- [x] Python captured-content retrieval;
- [x] CLI captured-content inspection;
- [x] versioned HTTP captured-content route;
- [x] preserved captured media type;
- [x] reuse of the existing digest-verified content read;
- [x] executable tests covering raw-content inspection and failure behavior.

**Exit condition:** A researcher can retrieve the exact immutable bytes associated with a persisted capture through Episteme's public Python, CLI, and HTTP surfaces, with explicit capture-root configuration, preserved media type, existing digest verification, deterministic failure behavior, and no change to the capture's epistemic status.

**Status:** Complete.


## Roadmap Rules/

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

**Phase 23 — Public Captured Content Inspection — Complete**
