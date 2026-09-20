# Episteme Execution History

**Status:** Canonical Phase 13 design
**Version:** 0.1
**Last updated:** 2026-09-19

## Purpose

Phase 12 made discovery workflows executable and inspectable, but workflow execution currently exists only in process memory. The epistemic artifacts produced by a workflow can persist while the account of the execution that produced them disappears.

Phase 13 establishes how execution history belongs in the durable scientific instrument.

## Central Question

**What happened to the history of the machine that produced this knowledge?**

The answer must preserve a distinction between epistemic artifacts, workflow definitions, and workflow executions. Execution history is scientific lineage metadata, not a new source of epistemic authority.

## Established Architectural Hole

Existing primitives do not cleanly carry complete workflow execution history:

- Transformation records reproducible operations over record identifiers, but workflow steps can consume and produce any existing Episteme artifact.
- Transformation requires record inputs and outputs, so using it for an entire workflow would lose real dependencies or falsely classify generated artifacts as records.
- DiscoveryTrail reconstructs discovery lineage from persisted artifacts. It is derived inspection, not an append-only record of a workflow execution, and it does not preserve workflow-level failure or execution identity.
- WorkflowExecution already contains the required execution semantics in memory, but currently has no durable persistence boundary.

The hole is therefore not merely a missing database table. It is the loss of an inspectable causal account between a declared workflow run and the artifacts it actually consumed and produced.

## Governing Invariant

**Execution history may explain how an artifact was produced; it may not upgrade what the artifact means.**

Persisting an execution must never:
- turn generated artifacts into grounded evidence;
- turn a workflow into a truth claim;
- imply that successful execution validates the scientific conclusions produced;
- replace artifact-level provenance;
- silently rewrite an execution after the fact.

## Proposed Boundary

The smallest justified durable boundary is:

**declared workflow → immutable workflow definition → execution occurrence → step lineage → existing Episteme artifacts**

A persisted workflow execution should retain workflow identity, workflow method/version, declared procedure semantics, declared starting inputs, ordered step definitions, actual effective step inputs, produced artifact identifiers, executed method/version, completion or failure state, failure location and reason, execution timestamps, and immutable execution identity.

A workflow definition is procedural metadata. A workflow execution is historical metadata. Neither is grounded scientific evidence.

## Definition Versus Execution

### Workflow definition

What was declared to run: identity, name, method/version, declared inputs, ordered steps, parameters, and assumptions.

### Workflow execution

What actually happened: execution identity, referenced workflow identity, execution status, step results, actual effective inputs, produced outputs, method/version actually recorded for each step, failure state, and execution timestamps.

A later revision of a workflow must not rewrite the historical execution of an earlier version.

## Persistence Rules

Execution history is append-only.

- Re-running a workflow creates a new execution identity.
- Existing execution history cannot be overwritten.
- Persisted step results are immutable.
- A failed execution remains inspectable.
- Previously completed steps remain visible after later failure.
- A persisted execution may reference artifacts persisted elsewhere; it does not copy or reinterpret their epistemic content.
- Missing referenced artifacts are a lineage integrity error, not an invitation to invent replacements.

## Reproducibility

Two executions may have different execution IDs and timestamps while retaining equal deterministic lineage when they use the same workflow definition, method/version, declared parameters, assumptions, starting state, effective inputs, and step method/version.

Execution history must therefore preserve both the historical occurrence and the timestamp-independent lineage representation already established by Phase 12.

## Public Inspection

If execution history is exposed publicly, it must be read-only and expose existing artifacts by identifier rather than create a parallel scientific representation.

A researcher should eventually be able to inspect what procedure was declared, what execution occurred, what each step consumed and produced, where execution stopped, which method/version ran, whether execution completed or failed, and how execution lineage relates to existing artifact lineage.

Public exposure is inspection, not endorsement.

## Relationship to Existing Provenance

Artifact provenance answers: **Where did this represented material come from?**

Workflow execution history answers: **Which declared computational procedure produced or connected these artifacts?**

These questions are complementary. Workflow execution should not be stuffed into ordinary source provenance merely because both concern history.

## Failure Semantics

Failure is durable information.

A failed execution must preserve workflow identity, execution identity, successful prior steps, failed step, exact effective inputs supplied to the failed step, method/version, failure classification/message, and execution timestamps.

No partial execution history may be erased merely because the workflow did not complete.

## Scope

Phase 13 is limited to durable, inspectable history for finite declared Episteme workflows.

It does not include autonomous research agents, workflow scheduling, distributed execution, laboratory control, workflow optimization, truth adjudication, workflow scoring, candidate ranking, automatic retry policy, external service provenance, or replacing existing artifact provenance.

## Initial Proof Targets

Before implementation is considered complete, executable tests should establish:
- a declared workflow can be persisted and recovered without semantic change;
- an execution can be persisted and recovered without semantic change;
- step input/output lineage survives process boundaries;
- method/version history survives persistence;
- failed executions preserve prior successful steps and the failure boundary;
- executions remain immutable;
- repeated executions receive distinct historical identities while retaining equal deterministic lineage when run against equal declared state;
- persisted execution history does not alter grounded/generated classification;
- existing discovery trails and artifact provenance remain independently valid;
- public inspection, if added in this phase, remains read-only and exposes execution history without creating a second epistemic model.

## Deferred Questions

The following should not be decided until implementation pressure requires them:
- whether workflow definitions need their own table or can be embedded in execution history;
- whether execution history should be linked into DiscoveryTrail;
- whether execution history should be queryable by produced artifact;
- whether public HTTP exposure is required immediately;
- retention or archival policy;
- cross-process or distributed execution identity;
- scheduling and orchestration services.

## Exit Condition

Phase 13 is complete when a finite declared workflow can be executed, persisted, recovered, and inspected after the original process has ended, with complete step lineage, method/version history, failure history, reproducibility semantics, and unchanged epistemic boundaries.

The resulting instrument should preserve not only **what Episteme knows**, but also **how Episteme came to produce the artifacts it produced**.

## Final Principle

**The history of an operation is evidence about the operation, not authority about its result.**
