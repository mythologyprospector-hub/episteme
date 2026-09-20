# Episteme Phase 14 — Public Execution Traceability

**Status:** Canonical Phase 14 design  
**Version:** 0.1  
**Last updated:** 2026-09-20

## Goal

Expose the durable execution history established by Phase 13 through Episteme's existing public inspection instrument, so a researcher can inspect not only the artifacts produced by a discovery workflow but also the declared procedure and historical execution that produced them.

Phase 14 closes a demonstrated boundary between:

- durable execution history inside the scientific instrument; and
- the read-only public surfaces that currently expose the scientific artifacts and discovery lineage.

This phase does **not** introduce a new epistemic layer.

## Established Architectural Hole

Phase 8's public instrument exposes grounded records, reviews, discovery trails, timestamp-independent discovery lineage, and deterministic discovery reports.

Phase 13 now durably preserves workflow definitions and workflow executions, including:

- workflow identity and declared procedure;
- execution identity;
- ordered step lineage;
- effective inputs and outputs;
- method and version history;
- completed and failed steps;
- historical execution timestamps;
- timestamp-independent execution lineage.

The current public Python API and HTTP API do not expose those durable workflow definitions or executions.

Therefore a public reader can currently reconstruct **what Episteme represents and the discovery trail around it**, but cannot use the public instrument to inspect the durable computational occurrence that produced or connected those artifacts.

The hole is not a missing execution model. Phase 13 established that model.

The hole is the missing **public inspection boundary** over that already-persisted execution history.

## Governing Invariant

**Public execution traceability may explain how an artifact was produced; it may not upgrade what the artifact means.**

Public exposure must never:

- turn execution success into scientific validation;
- turn workflow definitions into evidence;
- turn execution metadata into provenance for external truth;
- replace artifact-level provenance;
- imply that a workflow actually ran merely because its definition is inspectable;
- hide failed or partial executions;
- create a second persistence model.

## Architectural Boundary

Phase 14 extends the existing read-only public path:

**durable workflow definition/execution → public inspection API → CLI / HTTP transport**

The public layer reads the Phase 13 persistence boundary. It does not create another workflow store, execution log, or scientific representation.

The existing dependency direction remains:

**Episteme core → read-only public API → transport surfaces**

## Scope

Phase 14 is limited to public inspection of durable execution history.

### In scope

- read-only retrieval of a persisted workflow definition;
- deterministic listing of persisted workflow definitions where justified;
- read-only retrieval of a persisted workflow execution;
- deterministic listing of persisted workflow executions where justified;
- timestamp-independent execution lineage representation;
- CLI inspection of execution history;
- versioned HTTP read routes over the same public representations;
- explicit distinction between workflow definition, workflow execution, and epistemic artifacts;
- deterministic serialization and reproducible inspection;
- explicit handling of missing workflow/execution objects and operational failures;
- executable tests covering the public boundary.

### Out of scope

Phase 14 does not establish:

- public mutation of workflows or executions;
- authentication or authorization;
- scheduling;
- automatic retry;
- distributed execution;
- workflow optimization;
- autonomous research agents;
- laboratory control;
- execution scoring or ranking;
- truth adjudication;
- automatic scientific validation from execution success;
- a second workflow or execution persistence model;
- replacement of artifact-level provenance;
- automatic search or crawling;
- mandatory frontend infrastructure.

Those remain separate decisions unless later evidence establishes a need.

## Public Representation

The public representation should reuse the existing WorkflowDefinition, WorkflowExecution, and step-result semantics rather than define a parallel object model.

A workflow definition answers:

**What procedure was declared?**

A workflow execution answers:

**What occurrence of that procedure was recorded, and what happened at each step?**

An execution lineage answers:

**What timestamp-independent computational path does this execution represent?**

None of these answers:

**Was the scientific conclusion true?**

That question remains outside execution metadata.

## Public Python API

The public inspection layer should expose only read operations over persisted execution history.

The minimum justified operations are:

- retrieve one workflow definition by identifier;
- retrieve one workflow execution by identifier;
- list persisted workflow definitions in deterministic order;
- list persisted workflow executions in deterministic order.

Additional filtering, including lookup by produced artifact, is not part of the initial contract unless implementation evidence shows that the basic operations are insufficient.

The public API must preserve immutable historical identity and must not return mutable persistence handles.

## CLI Surface

The CLI should expose read-only inspection corresponding to the public Python API.

The initial command shape should remain consistent with the existing episteme inspection surface.

The CLI must not acquire mutation commands merely because workflow history is now publicly inspectable.

Execution inspection should make it possible to see:

- workflow identity and declared procedure;
- execution identity and status;
- ordered step results;
- effective inputs and outputs;
- method/version information;
- failure boundary when present;
- timestamp-independent lineage.

## HTTP Surface

The existing /api/v1 transport remains the public HTTP boundary.

Phase 14 should add read-only routes for durable workflow definitions and executions using the existing public representations.

The transport must preserve the existing rules:

- valid reads return 200 OK;
- malformed identifiers and unsupported query parameters return 400 Bad Request;
- missing objects return 404 Not Found;
- operational failures remain 500 Internal Server Error;
- mutation methods remain unsupported;
- object schema versions remain distinct from the HTTP transport version;
- returned execution metadata does not alter epistemic status.

The exact route and query contract must be documented before implementation.

## Relationship to Discovery Reports

Discovery reports and trails explain epistemic lineage.

Execution history explains computational occurrence.

They are complementary and should remain separate.

Phase 14 does not automatically insert workflow execution records into discovery trails. If later evidence shows that a researcher needs to navigate from an artifact to the execution that produced it, that is a separate architectural question.

The first Phase 14 contract should permit a researcher to inspect both sides independently without fabricating a relationship that Phase 13 did not establish.

## Failure Semantics

Failed executions are first-class historical occurrences.

Public inspection must preserve:

- successful steps before failure;
- the failed step;
- effective inputs supplied to that step;
- method/version;
- failure classification/message;
- execution identity and timestamps.

A public reader must not see a failed execution rewritten as absent, incomplete, or successful.

## Reproducibility

Repeated executions remain historically distinct.

Their execution identifiers and timestamps may differ while their timestamp-independent lineage representations remain equal when the declared workflow, effective inputs, outputs, methods, and status are equal.

Public inspection must expose enough of that representation to permit the same comparison already established by Phase 13.

## Proof Targets

Before Phase 14 is complete, executable tests should establish:

1. persisted workflow definitions are publicly retrievable without semantic change;
2. persisted workflow executions are publicly retrievable without semantic change;
3. deterministic listing order is stable where listing is provided;
4. execution lineage is exposed without fresh execution metadata altering the lineage representation;
5. failed execution history remains publicly inspectable;
6. public representations preserve workflow-definition versus execution distinction;
7. public exposure does not change grounded/generated artifact classification;
8. CLI inspection remains read-only;
9. HTTP inspection remains read-only and uses the existing error semantics;
10. the public execution surface does not create a second persistence or epistemic model.

## Exit Condition

Phase 14 is complete when a researcher using Episteme's documented public inspection surfaces can inspect a persisted workflow definition and a persisted workflow execution, reconstruct its ordered computational history, inspect its success or failure boundary, compare its timestamp-independent lineage, and relate those execution artifacts to existing Episteme artifacts without execution metadata acquiring epistemic authority.

## Final Principle

**A scientific instrument should let a researcher inspect not only what it produced, but also what procedure it recorded as having produced it — without confusing the history of the operation with evidence for the result.**
