# Autonomous Discovery Driver

**Status:** Experimental — Phase 27 implementation boundary  
**Version:** 0.2

## Why this exists

Phases 1–26 established the discovery substrate, finite workflow runner, external acquisition boundaries, public inspection surfaces, and Praxis evidence handoff. Phase 27 adds a bounded control loop that can observe represented state, select the next allowed investigation step, execute that step through host-owned capabilities, inspect the resulting state, and decide whether to continue or stop.

This is deliberately different from claiming that Episteme is already an autonomous scientist.

The driver is an instrument controller. A planner may propose the next bounded action. Episteme validates the action, executes it through declared host-owned runtimes, and returns the resulting state to the planner.

## Boundary

**represented state → planner → validated action → host-owned Episteme operation → new represented state → planner**

The planner does not receive authority to execute arbitrary Python, mutate the store directly, promote evidence, choose host runtime controls, or bypass the epistemic boundary.

## Action vocabulary

The Phase 27 driver permits exactly these actions:

- scout — request one host-owned bounded exploration operation;
- assess_exploration — request host-owned assessment of an exploration observation;
- admit_exploration — request host-owned admission of an accepted exploration observation;
- discover_gap — request host-owned structural-gap discovery;
- question — turn an existing finding into an unresolved question;
- hypothesis — create a generated hypothesis downstream of an existing finding;
- prediction — create a discriminating prediction from existing competing hypotheses;
- experiment — create and execute a bounded registered experiment through host-owned execution semantics;
- stop — terminate the bounded investigation with an explicit reason.

The exploration and structural-discovery actions are deliberately host-owned. The planner identifies what stage should happen next; it does not supply the grounded inputs, detector, position field, step, executor, admission policy, or other runtime controls.

## Exploration and structural discovery

The implemented Phase 27 exploration path is:

**scout → assess_exploration → admit_exploration → discover_gap**

The host binds these actions to bounded runtimes. The initial structural-discovery runtime uses the deterministic positional-gap detector.

A missing structural gap is a bounded failure. The planner cannot invent a gap merely because it wants to continue.

Generated exploration observations remain generated. Admission creates an explicit discovery finding representing the accepted observation; it does not convert the observation into grounded evidence.

The canonical structural-discovery boundary is documented in docs/autonomous-structural-discovery.md.

## Planner contract

A planner receives a compact, deterministic context containing grounded input identifiers, current findings, hypotheses, predictions, experiment proposals, evaluations, knowledge-state consequences, exploration observations and assessments, actions already taken, and bounded feedback from rejected actions.

It returns exactly one structured action.

A deterministic planner proves the control boundary and reproducibility. The Ollama planner provides a separate real-model acceptance layer.

## Validation and bounded correction

Every planner action is validated before execution.

Invalid or malformed actions are rejected explicitly. When retry budget remains, the rejection is returned to the planner as bounded feedback so it may correct the action.

The driver enforces:

1. a closed action vocabulary;
2. existence and semantic validity of referenced objects;
3. required rationale on every action;
4. host ownership of substantive runtime controls;
5. generated-versus-grounded separation;
6. finite step budgets;
7. bounded retry counts;
8. durable action/output traceability;
9. explicit termination.

The planner is steering, not authority.

## Experiment boundary

The planner may propose a bounded experiment, but execution remains host-owned.

The initial registered experiment runtime performs only declared operations. The Phase 27 acceptance path uses a positional-presence experiment over host-selected records and evaluates the resulting observation against the declared prediction boundary.

An experiment result is a result. Its evaluation remains generated interpretation and does not silently become a universal verdict.

## Acceptance

Phase 27 has two distinct acceptance layers.

### Deterministic control-boundary proof

A deterministic injected planner demonstrates that Episteme can complete a bounded investigation without a human selecting every intermediate action.

### Real-model acceptance

scripts/accept_ollama_full_chain.py exercises the same boundary with a real Ollama model. The acceptance requires the model-backed run to complete cleanly with a final experiment followed by bounded termination.

A passing model-backed run demonstrates that the concrete planner can operate inside the boundary. It does not demonstrate general scientific intelligence.

## Explicit non-claims

Phase 27 does not claim:

- general scientific intelligence;
- autonomous truth discovery;
- unrestricted research;
- unbounded web research or crawling;
- automatic laboratory control;
- scientific importance ranking;
- automatic truth adjudication;
- that a language model's output is evidence;
- that generated exploration becomes grounded evidence;
- that a successful bounded run proves the scientific correctness of its hypotheses.

## Architectural invariant

> **The planner may choose among declared bounded operations, but only host-owned Episteme capabilities determine what those operations actually do.**

The control loop is therefore an orchestration boundary, not a new epistemic authority.
