# Phase 24 — Acquisition Execution / Workflow Integration

**Status:** Canonical design  
**Phase:** 24  
**Depends on:** Phase 12 Workflow Orchestration; Phase 13 Execution History; Phase 19 Captured Representation; Phase 20 External Acquisition

## Goal

Make bounded external acquisition executable as a declared Episteme workflow operation while reusing the existing workflow and execution-history machinery.

The phase answers:

> How can a declared Episteme procedure perform an acquisition and preserve both the procedure's execution history and the external acquisition history?

## Pressure

Phase 20 explicitly established that acquisition may later be invoked as a workflow step. Phases 12 and 13 already provide finite workflow definitions, step execution, and durable execution history.

The missing seam was not another workflow engine. It was the ability for workflow lineage to reference the operational CapturedRepresentation produced by an acquisition step.

## Core Invariant

> **Workflow execution records what the declared Episteme procedure did; acquisition history records what the external source supplied. A workflow reference to a capture does not turn that capture into an epistemic artifact.**

## Minimal Integration

The existing WorkflowStep and WorkflowStepResult identifier fields are reused.

A workflow step may consume or produce:

- existing epistemic artifacts; or
- operational resources such as persisted captured representations.

No new workflow step type, execution model, acquisition-history model, or relationship graph is introduced.

The existing Store validation boundary is widened only enough to recognize persisted captures as valid workflow lineage resources.

## Acquisition Workflow Path

The bounded vertical path is:

**declared workflow → acquisition step → existing acquire() operation → persisted capture → workflow execution history**

The acquisition operation remains responsible for provider request, response outcome, capture creation, and exact content persistence. The workflow runner remains responsible for ordered execution and recording the resulting capture identifier.

## Failure Semantics

An external provider failure is an acquisition outcome, not necessarily a workflow execution failure.

When acquisition successfully performs its own contract and persists a FAILED capture, the workflow step may complete with that capture as its output. This preserves two facts without conflating them:

- the declared Episteme operation executed successfully;
- the external acquisition produced a failed outcome.

If the workflow executor itself fails before or outside successful acquisition persistence, existing Phase 13 workflow-step failure semantics remain unchanged.

## Reproducibility

Workflow execution identity remains distinct from acquisition identity.

Repeated workflow executions are distinct execution events. Repeated acquisition events remain distinct captures even when their content is identical.

The captured representation remains the identity anchor for the exact external material received.

## Epistemic Boundary

A capture referenced by workflow execution remains operational acquisition history. The workflow does not promote it to evidence, a grounded record, a claim, a hypothesis, or a discovery finding.

An existing source adapter may subsequently interpret the capture into grounded records, with Phase 22 capture-linked provenance preserving the exact supplied capture.

## Scope

Phase 24 establishes:

- acquisition as an executable workflow operation;
- workflow lineage references to persisted captures;
- preservation of successful and failed acquisition outcomes;
- reuse of existing WorkflowDefinition, WorkflowStep, WorkflowExecution, and Store machinery;
- tests proving the acquisition-to-workflow boundary.

## Out of Scope

Phase 24 does not establish autonomous research, autonomous crawling, scheduling, background harvesting, new acquisition providers, a new execution engine, a new acquisition-history model, promotion of captures to evidence, workflow-driven interpretation, ranking, relevance scoring, or distributed execution.

## Exit Condition

A finite declared workflow can invoke the existing bounded acquisition operation, record the resulting capture identifier in execution lineage, persist the workflow execution, and preserve the independent acquisition outcome and content without changing epistemic status.
