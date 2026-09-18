# Episteme Roadmap

**Status:** Canonical planning document  
**Version:** 1.6  
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

- [x] experiment result ingestion
- [x] explicit result-to-prediction evaluation
- [x] failed-prediction recording
- [x] explicit knowledge-state consequences
- [x] iterative discovery
- [x] renewed evaluation-conflict discovery
- [x] reproducible discovery trails

**Exit condition:** A complete discovery cycle can run from grounded evidence through hypothesis, prediction, experiment, result, result evaluation, explicit knowledge-state consequence, and renewed discovery while preserving the distinction between observation and interpretation.

### Phase 6 Exit Audit

The implemented Phase 6 behavior satisfies the stated exit condition:

- grounded result ingestion remains separate from generated evaluation;
- prediction evaluations preserve the compared result and prediction identifiers, conditions, assumptions, outcome, rationale, and method/version;
- failed predictions are represented as `inconsistent` evaluations without mutating predictions;
- explicit knowledge-state consequences accumulate as generated, append-only artifacts without becoming truth flags;
- renewed discovery can inspect generated evaluation state while preserving grounded evidence in `input_ids`;
- reproducible discovery trails reconstruct explicit lineage from renewed findings back through evaluations, results, predictions, proposals, hypotheses/models, motivating findings, and grounded inputs;
- trail construction is read-only and fails explicitly when required lineage is missing;
- the trail implementation provides a timestamp-independent canonical lineage representation for reproducibility comparison.

The audit found no Phase 6 capability that requires new machinery before advancing. Domain broadening is therefore the next roadmap phase.

### Phase 6 Architecture Decision

The Phase 6 audit established that the existing result, relationship, lifecycle, evidence-assessment, and transformation primitives do not by themselves represent the semantic comparison between a result and a prediction.

Phase 6 therefore requires a distinct generated **result evaluation** concept rather than overloading evidence assessment or lifecycle events.

The evaluation is contextual and non-binary: **consistent**, **inconsistent**, or **inconclusive** under stated conditions and assumptions. It does not become evidence, does not rewrite the result or prediction, and does not constitute a universal truth or confidence score.

"Knowledge-state update" is defined as an explicit accumulation of evidence, relationships, evaluations, lifecycle events, and generated revisions. It is not a mutable universal truth flag.

The Phase 6 implementation now treats an explicit knowledge-state consequence as a separate generated artifact derived from one or more prediction evaluations. The consequence is contextual and append-only: supports, weakens, contradicts, or leaves_unresolved under stated assumptions. It does not mutate the target or establish a universal truth value.

The implementation must preserve the evaluation identifiers, target identifier, consequence classification, assumptions, rationale, method/version, timestamp, and schema version so the transition can be reconstructed.

The first closed-loop discovery seam is now explicit: discovery findings may preserve generated Phase 6 objects as `context_ids` while keeping grounded/integrity evidence in `input_ids`. This permits renewed discovery to inspect accumulated evaluations and consequences without promoting generated state to evidence. The first renewed-discovery algorithm is now documented as conservative evaluation-conflict detection and is implemented and tested.



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

Domains must be selected for architectural pressure rather than spectacle. The first domain should establish a clean extension point; the second should stress that extension point with materially different evidence structure.

**Exit condition:** Two materially different scientific domains can use domain-specific layers while preserving the same core semantics for evidence, inference, unknowns, results, evaluations, and reproducibility.

### Phase 7 Exit Audit

The Phase 7 implementation and cross-domain stress tests satisfy the stated exit condition.

- Astronomy uses the stable `MEASUREMENT` primitive for quantitative domain structure.
- Biology uses the stable `OBSERVATION` primitive for categorical and structured domain evidence.
- Domain-specific schemas remain in domain adapters rather than the core model.
- Both adapters preserve caller-supplied provenance and pass records through ordinary core persistence and validation.
- Missing, unreported, unresolved, conflicting, and uncertain states remain explicit within their respective domain semantics; Astronomy uncertainty metadata remains domain-owned.
- Generated findings, hypotheses, predictions, proposals, and evaluations remain distinct from grounded records.
- A mixed Astronomy/Biology fixture traverses the existing closed discovery loop and is reconstructed by the existing reproducible trail machinery.
- No new core epistemic primitive, domain-specific core branch, or universal domain rule was required.

The cross-domain stress test is implemented in `tests/test_phase7_cross_domain.py`. The complete local suite reached 74 passing tests after this implementation.

Phase 7 therefore satisfies its exit condition. Further domain-specific expansion is not required before advancing; additional domains remain appropriate as future architecture stress tests rather than prerequisites for Phase 7 completion.

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
- [ ] collaboration and review workflows
- [ ] documented external HTTP/API surface
- [ ] transparent public evaluation workflow

The exact public product shape remains intentionally open.

### Phase 8 Public Knowledge Import Audit

The first public knowledge-import capability satisfies its documented initial scope.

- a finite caller-supplied Crossref representation is translated by an explicit source-specific adapter;
- external work metadata remains a grounded `SOURCE` record rather than being promoted to observation, measurement, or generated interpretation;
- DOI-derived deterministic UUID identity preserves the core record identity invariant;
- source location, capture time, source publication-date metadata where available, and adapter/version are preserved as provenance/translation context;
- the complete input batch is validated before persistence, preventing partial writes from malformed later items;
- repeated deterministic identities are rejected by ordinary immutable store insertion rather than silently overwritten;
- deterministic translation, source preservation, malformed DOI rejection, and batch atomicity are tested;
- no web crawler, ranking system, semantic deduplication mechanism, or new epistemic primitive was introduced.

The initial public knowledge-import capability is therefore complete. Broader external-source support remains open as future work and is not implied by this milestone.

### Phase 8 Collaboration/Review Audit

The initial collaboration/review capability is complete. Reviews are immutable records over existing Episteme objects, preserve reviewer/process provenance and disagreement, validate their target before persistence, and do not mutate or reclassify the reviewed object. The read-only Python API and installed CLI expose review inspection with exact target-kind/identifier scoping. Review records remain outside discovery trails because they are collaboration metadata rather than epistemic lineage nodes.

### Phase 8 Initial Implementation Audit

The first Phase 8 implementation satisfies the initial public-instrument exit condition.

- the read-only Python API exposes grounded record inspection, deterministic listing, trail reconstruction, lineage, and reports;
- the installed CLI exposes the same inspection surface without mutation commands;
- discovery reports preserve grounded records separately from generated artifacts;
- the browser renderer exposes the same report data without creating a second epistemic representation;
- generated artifacts expose their `via`, method, and rationale in the browser surface so a researcher can inspect why each step exists;
- full trail and timestamp-independent reproducible lineage remain available;
- the complete closed discovery cycle is exercised by the public acceptance test;
- no new persistence model, epistemic primitive, autonomous authority, or external service was required.

This audit closes the initial Phase 8 public-instrument milestone. It does not close Phase 8 as a whole; the remaining public capabilities stay explicitly open on the roadmap.

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

**Phase 8 — Public Scientific Instrument**

Phase 1 is complete. The grounded substrate, provenance boundary, relationships, deterministic serialization, validation, SQLite persistence, and externally grounded ingestion fixture are implemented and verified.

Phase 2 is complete. The substrate now has explicit provenance validation, contradiction representation, contextual evidence assessment, immutable records, append-only lifecycle history, explicit state transitions, and reproducible transformations.

Phase 3 is complete. Discovery findings can be traced to grounded inputs, expectation-based gaps preserve their exact basis, explicit contradictions are surfaced without semantic invention, bounded questions can be generated from supported findings, interpretable measures are recorded, and generated findings remain outside the grounded evidence boundary.

Phase 4 is complete. Hypotheses, models, assumptions, competing explanations, and distinguishing predictions are represented and verified.

Phase 5 is complete. Experiment proposals explain why proposed observations could discriminate among competing explanations, actual results remain grounded and independently sourced, and explicit result-to-proposal/prediction relationships preserve the distinction between prediction, proposed test, and observed result.

Phase 6 is complete. Result records can be ingested through the grounded JSONL ingestion boundary; prediction evaluations represent result-to-prediction comparison; failed predictions are represented by `inconsistent` evaluations rather than mutation; explicit knowledge-state consequences are persisted; renewed discovery can surface differing evaluation outcomes while keeping generated context separate from grounded evidence; and reproducible discovery trails can reconstruct a complete cycle as an auditable lineage. The Phase 6 exit condition is satisfied.

Phase 7 is complete. Astronomy and Biology demonstrate materially different evidence shapes above the stable core, while provenance, explicit unknown/conflict/uncertainty states, generated-versus-grounded boundaries, closed-loop lineage, and reproducibility remain intact. The Phase 7 exit condition is satisfied.

Phase 8 has established its first researcher-facing public instrument and its initial public knowledge-import capability: a read-only Python inspection API, the installed `episteme` command, deterministic discovery reports, and a self-contained browser-readable report renderer. These expose existing Episteme state rather than creating a parallel public data model. The Phase 8 initial implementation exit condition is satisfied: a person outside the development workflow can inspect a complete representative discovery cycle and reconstruct why generated steps exist without losing the grounded/generated boundary. Collaboration/review workflows, a documented external HTTP/API surface, and a transparent public evaluation workflow remain open Phase 8 work. Broader source import remains future work beyond the initial Crossref capability.
