# Phase 29 — Rediscovery

**Status:** Implementation underway — bounded rediscovery path under active verification

## Purpose

Phase 29 is the first phase whose primary proof is not another piece of infrastructure.

Episteme must demonstrate that the existing discovery machinery can reproduce a meaningful historical scientific discovery pattern:

**earlier evidence → structural gap → candidate explanation → prediction → later held-out evidence → deterministic evaluation**

The system must not be given the historical discovery answer, the later object's identity, or a rule written specifically to produce the answer.

## Canonical benchmark

The first benchmark is a bounded **Mendeleev-style rediscovery** using the history of the periodic table.

The fixture represents only information available before the later discovery of the element historically identified as germanium. The later element is held out as the evaluation target.

The benchmark is deliberately bounded. It is not intended to recreate all of nineteenth-century chemistry. It tests whether Episteme can:

1. inspect the earlier represented observations;
2. identify a structural vacancy or unresolved pattern;
3. preserve that gap as distinct from evidence;
4. generate one or more candidate explanations;
5. make a quantitative, testable prediction about the missing case;
6. reveal the held-out later observation only through the normal evidence/experiment boundary;
7. deterministically compare the prediction with the later observation;
8. preserve the complete lineage, including success or failure.

## Anti-cheating rules

The benchmark is invalid if the answer is smuggled into the fixture or runtime.

Therefore:

- the planner input must not contain the later element's name;
- the planner input must not contain its modern atomic number;
- the planner input must not contain its later-discovered measured properties;
- the benchmark must not include a hidden instruction such as "predict germanium";
- the evaluator may know the held-out record, but the discovery path may not;
- the evaluator may grade a prediction, but it may not manufacture a successful prediction;
- historical facts used as fixture data must be explicitly dated or otherwise identified as pre-discovery material;
- generated hypotheses and predictions remain generated artifacts until later evidence is ingested and evaluated;
- a passing run must be reproducible from the same pre-discovery fixture and method versions.

## What counts as a prediction

A prediction must contain values that could have been wrong before the held-out evidence is revealed.

A useful first target is a bounded set of numerical properties rather than a claim of exact historical reconstruction. The benchmark should pre-register acceptable tolerances before the held-out record is exposed.

The prediction must therefore be more than:

> "There should be something here."

It must say, in machine-checkable form, what the missing case should look like.

## Evaluation

Evaluation is deterministic and host-owned.

The evaluator receives:

- the pre-registered prediction;
- the held-out grounded observation;
- the declared comparison method and tolerances.

It produces an explicit result such as:

- prediction matched;
- prediction partially matched;
- prediction failed.

No universal "truth", "plausibility", or "intelligence" score is introduced.

## Execution boundary

The rediscovery benchmark must use the existing architecture:

**grounded historical fixture → discovery → hypothesis → prediction → bounded experiment/evidence request → held-out grounded observation → deterministic evaluation**

The planner may select bounded actions. It may not:

- read the held-out answer early;
- execute arbitrary code;
- access the network directly;
- create grounded evidence;
- alter the evaluator;
- bypass the declared experiment boundary.

## Implementation stages

### Stage 1 — Fixture and benchmark contract

Create a small pre-discovery historical dataset and an opaque held-out record.

Write executable tests proving that the held-out answer is inaccessible before the evaluation boundary.

### Stage 2 — Deterministic rediscovery path

Build the smallest host-owned runtime needed to turn the established gap into a quantitative prediction and evaluate it against the held-out observation.

Do not add general chemistry infrastructure.

### Stage 3 — Autonomous acceptance

Connect the existing Ollama planner to the benchmark.

The acceptance harness must demonstrate a bounded action trace that reaches a prediction, obtains the held-out evidence through the host boundary, and receives a deterministic evaluation.

### Stage 4 — Failure proof

Deliberately alter or corrupt the held-out observation and demonstrate that the same pre-registered prediction fails rather than being retroactively adjusted.

## Phase 29 exit condition

Phase 29 is complete when an executable, reproducible benchmark demonstrates that Episteme can independently move from pre-discovery historical evidence to a non-trivial quantitative prediction and then correctly evaluate that prediction against later held-out evidence, while preserving:

- grounded-versus-generated separation;
- host ownership of substantive operations;
- bounded autonomous execution;
- immutable provenance and lineage;
- deterministic evaluation;
- explicit failure;
- reproducibility.

A successful run is evidence that the architecture can support rediscovery. It is **not** evidence that Episteme has achieved general scientific intelligence.

## Acquisition boundary

Phase 29 deliberately does **not** claim that Episteme can autonomously acquire a genuinely new scientific observation from the outside world. The held-out Mendeleev record is pre-supplied as a benchmark fixture and is revealed only at the host-owned experiment/evaluation boundary. This proves separation, execution, and evaluation; it does not prove that Episteme can operate an instrument, query a live scientific database for a novel measurement, or otherwise create a new observation.

Phase 28 already provides bounded external acquisition, but its currently registered capability is Crossref metadata. That is useful for evidence retrieval, not a general scientific-observation capability. A future observation-acquisition capability should be added only when a concrete benchmark requires one and its source, measurement semantics, provenance, and independence rules can be specified explicitly.

This limitation is therefore a declared Phase 29 boundary, not a hidden success criterion.

## What comes next

Only after this benchmark passes should the project generalize the rediscovery machinery to another historical domain such as astronomy, or introduce a concrete observation-acquisition capability for a benchmark that actually requires new observations.

