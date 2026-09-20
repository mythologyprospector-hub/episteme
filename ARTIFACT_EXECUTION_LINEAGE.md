# Phase 15 — Artifact-to-Execution Lineage

## Goal

Make the relationship between persisted Episteme artifacts and the workflow executions that consumed or produced them directly inspectable through the existing read-only public instrument.

Phase 13 established durable execution history. Phase 14 exposed that history publicly. Phase 15 closes the remaining navigation gap without creating a second provenance model.

## Architectural pressure

A persisted workflow execution already records the effective input and output identifiers for each step. A researcher can therefore inspect:

**workflow → execution → step → artifact**

but there is no canonical reverse inspection path:

**artifact → execution(s) → step(s)**

Without that reverse path, execution history remains discoverable only by searching executions externally.

## Boundary

Phase 15 establishes a read-only reverse index operation over the existing Phase 13 execution history:

**existing artifact → persisted workflow execution(s) that consumed or produced it**

The relationship is derived from existing `WorkflowStepResult.input_ids` and `WorkflowStepResult.output_ids`. It is not a new persisted relationship and does not alter either the artifact or execution.

## Governing invariant

> **Execution linkage may explain which recorded execution consumed or produced an artifact; it may not upgrade what the artifact means.**

Execution linkage is computational history, not provenance, evidence, confidence, validation, or truth.

## Semantics

An artifact is linked to an execution when its identifier appears in any persisted workflow step result's:

- `input_ids`;

- `output_ids`.

The public result reuses the existing persisted `WorkflowExecution` representation. No execution is copied into a second model.

A single execution appears at most once in the artifact's result, even if the artifact occurs in multiple steps.

Results use the existing deterministic execution ordering.

Unknown artifact identifiers are treated as missing resources rather than as empty known histories.

## Public surface

Python:

- `list_workflow_executions_for_artifact(store, artifact_id)`

CLI:

- `episteme --store <path> artifact-executions <artifact_id>`

HTTP:

- `GET /api/v1/artifacts/{artifact_id}/executions`

The HTTP route is read-only and uses the existing `/api/v1` error and serialization conventions.

## Relationship to provenance

Phase 15 does not modify `Record.provenance`, relationship provenance, transformation provenance, or any other existing provenance representation.

An artifact may have provenance without being associated with a workflow execution, and a workflow execution may reference an artifact without changing that artifact's provenance.

These answer different questions:

- provenance: **where did this represented material come from?**

- execution linkage: **which recorded computation consumed or produced this artifact?**

Neither answer grants authority to the other.

## Relationship to execution lineage

Phase 15 is complementary to Phase 14.

Phase 14 answers:

**what happened during this execution?**

Phase 15 additionally answers:

**which executions reference this artifact?**

The timestamp-independent execution lineage representation remains unchanged. Execution identity and timestamps remain historical metadata and do not enter the lineage representation.

## Scope

In scope:

- reverse lookup over existing persisted workflow executions;

- input and output artifact matching;

- deterministic result ordering;

- read-only Python, CLI, and HTTP inspection;

- missing-artifact semantics;

- executable tests proving the boundary.

Out of scope:

- a new artifact model;

- a new provenance model;

- a persisted reverse-index table;

- execution scoring or trust;

- automatic causal inference;

- artifact mutation;

- execution mutation;

- scheduling or retries;

- distributed execution;

- truth adjudication;

- automatic validation of scientific results;

- workflow optimization;

- autonomous agents.

## Exit condition

A researcher can start from an existing Episteme artifact and inspect every persisted workflow execution that consumed or produced it, including the relevant step-level input/output history, through the same read-only public instrument used for Phase 14, without changing artifact meaning, provenance, or execution semantics.