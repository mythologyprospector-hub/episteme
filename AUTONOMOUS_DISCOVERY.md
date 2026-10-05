# Autonomous Discovery Driver

**Status:** Experimental — Phase 27 implementation boundary
**Version:** 0.1

## Why this exists

Phases 1–26 established a substantial discovery substrate and a finite workflow runner. The missing capability is a control loop that can observe represented state, decide what bounded investigation step should happen next, execute only an allowed operation, inspect the resulting state, and decide whether to continue or stop.

This is deliberately different from claiming that Episteme is already an autonomous scientist.

The driver is an instrument controller. A planner may propose the next bounded action. Episteme validates the action, executes it through declared adapters, and returns the resulting state to the planner.

## Boundary

represented state → planner → validated action → declared Episteme operation → new represented state → planner

The planner does not receive authority to execute arbitrary Python, mutate the store directly, promote evidence, or bypass the epistemic boundary.

The planner may only select from the driver's explicit action vocabulary.

## First action vocabulary

- question — turn an existing gap or tension into an unresolved question;
- hypothesis — create a generated hypothesis downstream of an existing finding;
- prediction — create a discriminating prediction from existing competing hypotheses;
- experiment — propose a discriminating experiment from existing predictions;
- stop — terminate the investigation with an explicit reason.

Grounded result ingestion and external acquisition remain separate capability boundaries. The driver may stop at an experiment proposal rather than pretending that an observation occurred.

## Planner contract

A planner receives a compact, deterministic context containing grounded input identifiers, current findings, current hypotheses, current predictions, current experiment proposals, and actions already taken in this run.

It returns exactly one structured action.

A model-backed planner can therefore be added without embedding a model provider into Episteme's epistemic core. A deterministic planner can be used for tests and reproducibility.

## Safety and epistemic rules

The driver must:

1. reject unknown action kinds;
2. require referenced objects to exist;
3. permit only the declared action vocabulary;
4. preserve generated-versus-grounded distinctions;
5. preserve the planner's rationale and method/version;
6. reject malformed planner output and, when retry budget remains, feed the rejection back to the planner for bounded correction;
7. enforce a finite step budget;
8. never treat planner text as evidence;
9. never execute arbitrary code supplied by a planner;
10. preserve every completed action and its outputs in the execution trace.

The planner is steering, not authority.

## What counts as success

This phase is successful only when an injected planner can drive a complete bounded investigation without a human selecting each intermediate step.

The first acceptance test should use a small scientific fixture where the starting evidence establishes a bounded gap, the planner receives the gap rather than a pre-written workflow, the planner chooses the next action, the driver validates and executes it, the resulting state is returned to the planner, and the loop reaches an experiment proposal.

A real model-backed run is a separate acceptance layer. A passing fake-planner test proves the control boundary; it does not prove scientific autonomy.

## Explicit non-claims

This phase does not claim general scientific intelligence, autonomous truth discovery, unrestricted research, automatic laboratory control, unbounded web research, scientific importance ranking, automatic truth adjudication, or that a language model's output is evidence.
