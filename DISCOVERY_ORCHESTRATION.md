# Episteme Discovery Orchestration

**Status:** Complete — Canonical Phase 12 design
**Version:** 0.1
**Last updated:** 2026-09-19

## Purpose

Phase 12 addresses the next architectural pressure revealed after the first eleven phases:

Episteme now contains the primitives required to ingest grounded material, establish structural gaps, generate candidate completions, design discriminating experiments, evaluate results, and renew discovery. What remains fragmented is the reproducible execution boundary that connects those existing operations into an inspectable discovery run.

The goal is not to add another epistemic object.

The goal is to make an existing chain executable as a workflow without hiding which operations occurred, which inputs they consumed, and which generated artifacts they produced.

## Core Invariant

**Orchestration may coordinate epistemic operations; it may not manufacture epistemic authority.**

A workflow runner may invoke ingestion, discovery, candidate, prediction, experiment, evaluation, and reporting operations. It must not reinterpret generated output as grounded evidence, silently choose among competing explanations, or erase intermediate artifacts.

## The Pressure

The current system can represent the complete discovery loop, but its operations remain primarily callable as individual primitives.

That creates a practical boundary:

**represented capability is not yet reproducible execution.**

A researcher should be able to say:

> Run this defined discovery procedure against this represented state.

and later inspect:

- what procedure ran;
- which method/version was used at each step;
- which grounded inputs were read;
- which generated artifacts were produced;
- where the run stopped or branched;
- what downstream artifacts resulted.

This is an execution and lineage problem, not a new knowledge model.

## Proposed Boundary

The initial Phase 12 flow is:

**represented state → declared workflow → existing Episteme operations → generated artifacts + execution lineage**

The workflow itself is a procedure description.

It is not evidence, a hypothesis, a prediction, or a scientific conclusion.

## Workflow Requirements

A first workflow boundary should preserve:

- workflow identity;
- workflow method and version;
- declared starting inputs;
- ordered operations;
- operation parameters;
- assumptions;
- execution timestamps;
- produced artifact identifiers;
- validation or completion state;
- failure state when execution stops;
- reproducibility metadata.

The workflow must be inspectable after execution.

## Grounded Boundary

Workflow execution must preserve the existing distinction between grounded and generated material.

A workflow may consume grounded records.

A workflow may produce generated artifacts.

A workflow must never make a generated artifact grounded merely because a later workflow step consumes it.

When a workflow consumes a new external result, that result must enter through the existing grounded ingestion boundary.

## Existing Primitives First

Phase 12 should compose existing primitives before introducing new ones.

Potentially reusable operations include:

- grounded ingestion;
- structural-gap detection;
- candidate completion;
- candidate constraint assessment;
- discriminating prediction;
- experiment proposal;
- grounded result ingestion;
- prediction evaluation;
- knowledge-state consequence;
- renewed discovery;
- discovery trails.

A new core primitive is justified only if execution lineage cannot be represented cleanly using existing semantics.

## Determinism

A workflow should be reproducible relative to:

- the represented starting state;
- workflow method and version;
- operation parameters;
- selected input identifiers;
- explicit assumptions;
- existing operation method/version metadata.

Execution timestamps and fresh artifact identifiers are generation metadata and must not be treated as semantic inputs to reproduction.

If the underlying represented state changes, a later execution may legitimately produce different artifacts.

## Branching and Alternatives

Workflow orchestration must not collapse alternatives.

If candidate A and candidate B both enter a workflow, their branches remain inspectable.

A workflow may terminate a branch because an explicit operation failed, a required artifact is absent, or a declared condition is not satisfied.

It must not silently discard an alternative because another branch appears preferable.

## Failure

Failure is an inspectable workflow state.

A failed operation must preserve:

- the operation that failed;
- its declared inputs;
- its method/version;
- the failure classification;
- artifacts already produced before failure.

A failed workflow does not erase prior grounded or generated artifacts.

## No Universal Ranking

Phase 12 does not introduce:

- a universal workflow score;
- a universal candidate ranking;
- autonomous truth selection;
- an importance score;
- a global confidence score;
- automatic selection of the “best” discovery path.

Workflow branching and selection, when eventually required, must use explicit declared rules.

## Scope

Phase 12 begins with finite, explicitly declared workflows over represented Episteme state.

It does not include:

- autonomous open-ended research agents;
- unrestricted web crawling;
- automatic laboratory control;
- universal scientific planning;
- hidden model-provider state;
- global optimization of scientific discovery;
- automatic truth adjudication.

Those remain separate architectural questions.

## Initial Proof Target

The first implementation should demonstrate one complete reproducible workflow using existing primitives:

1. start from grounded records;
2. establish a structural gap;
3. generate competing candidate completions;
4. create discriminating predictions;
5. create an experiment proposal;
6. ingest a grounded result;
7. evaluate the predictions;
8. record knowledge-state consequences;
9. renew discovery;
10. preserve inspectable execution lineage throughout.

The workflow must not require a new epistemic primitive merely to connect these steps.

## Exit Condition

Phase 12 is complete when Episteme can execute a declared finite discovery workflow that:

- composes existing epistemic primitives;
- preserves grounded/generated distinctions;
- records ordered execution lineage;
- preserves alternatives and intermediate artifacts;
- records explicit failures without erasure;
- is reproducible relative to its declared state, parameters, assumptions, and method versions;
- can be inspected after execution;
- is demonstrated by executable tests.

The purpose of Phase 12 is not to make Episteme autonomous.

The purpose is to make the discovery machinery **run as a traceable instrument rather than remain a collection of disconnected capabilities**.
