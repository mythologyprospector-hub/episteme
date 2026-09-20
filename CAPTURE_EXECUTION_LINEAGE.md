# Episteme Phase 25 — Capture-to-Execution Lineage

**Status:** Canonical Phase 25 design  
**Version:** 0.1  
**Last updated:** 2026-09-20

## Goal

Make the relationship between a persisted captured representation and the workflow executions that consumed or produced it directly inspectable through the existing read-only public instrument.

Phase 24 established that captured representations may participate in workflow execution lineage as operational resources. Phase 15 already established the corresponding reverse lookup for existing Episteme artifacts.

Phase 25 closes the navigation gap created by that integration without creating another lineage model.

## Architectural Pressure

A researcher can already inspect:

**capture → capture metadata/content**

and:

**workflow → execution → step → resource**

Phase 24 makes a capture a valid resource in the second path, but there is no direct canonical reverse path:

**capture → execution(s) → step(s)**

Without that path, acquisition operations can produce durable execution history while a researcher must search executions externally to discover which executions referenced a particular capture.

## Boundary

Phase 25 establishes a read-only reverse lookup over existing persisted workflow executions:

**existing captured representation → persisted workflow execution(s) that consumed or produced it**

The relationship is derived from existing WorkflowStepResult.input_ids and WorkflowStepResult.output_ids. It is not a new persisted relationship or reverse-index table.

## Governing Invariant

> **Capture-to-execution linkage explains which recorded computation consumed or produced a captured representation; it does not upgrade the captured representation into epistemic evidence or authority.**

A capture remains an operational record of external acquisition.

## Semantics

A capture is linked to an execution when its identifier appears in any persisted workflow step result's:

- input_ids;
- output_ids.

The public result reuses the existing WorkflowExecution representation.

A single execution appears at most once because the underlying execution is yielded once when any step references the capture.

Results retain existing deterministic execution ordering.

A missing capture is treated as a missing public resource rather than as an empty execution history.

## Public Surface

Python:

- list_workflow_executions_for_capture(store, capture_id)

CLI:

- episteme --store <path> capture-executions <capture_id>

HTTP:

- GET /api/v1/captures/{capture_id}/executions

All surfaces are read-only.

## Relationship to Phase 15

Phase 15 provides:

**artifact → execution(s)**

Phase 25 provides:

**capture → execution(s)**

The two operations share the existing persisted execution history but preserve the distinction between epistemic artifacts and operational captures.

No second reverse index is introduced.

## Relationship to Acquisition and Provenance

Acquisition history answers:

**What did the external source supply, and what happened during acquisition?**

Workflow execution history answers:

**What did the declared Episteme procedure record as happening?**

Grounded provenance answers:

**What captured representation supplied a grounded record?**

Phase 25 does not merge these questions.

A workflow execution referencing a capture does not become provenance for external truth, and the capture does not become evidence merely because a workflow consumed it.

## Failure Semantics

A persisted failed capture may still be referenced by a completed acquisition workflow execution when the acquisition operation successfully executed and recorded the external failure as its result.

Phase 25 exposes that existing relationship without rewriting either outcome.

If workflow execution itself fails before producing a capture reference, existing execution-failure semantics remain unchanged.

## Scope

In scope:

- reverse lookup from a persisted capture to workflow executions;
- matching existing step inputs and outputs;
- deterministic execution ordering;
- explicit missing-capture semantics;
- read-only Python, CLI, and HTTP inspection;
- executable tests.

Out of scope:

- new persistence models;
- new reverse-index tables;
- new provenance models;
- acquisition retries or scheduling;
- autonomous acquisition;
- interpretation of captured content;
- evidence promotion;
- execution scoring or ranking;
- workflow optimization;
- mutation;
- distributed execution.

## Exit Condition

A researcher can start from an existing captured representation and inspect every persisted workflow execution that consumed or produced it through the same read-only public instrument, while preserving capture identity, acquisition semantics, workflow history, provenance, and epistemic boundaries.