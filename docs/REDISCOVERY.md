# Phase 29 — Rediscovery

**Status:** Phase 29 implementation merged; review-2 hardening is under verification

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


## Review-3 benchmark rules

The rediscovery benchmark does not treat model step completion as a scientific pass.

For each property case, the host computes a pre-registered baseline: the arithmetic midpoint of the two observed neighbours immediately surrounding the missing period. The model may use a different method. A forecast is individually consistent only when it is within the pre-registered tolerance and its error is no worse than the host baseline.

A competing-hypothesis case passes its forecast criterion when at least one forecast is individually consistent. Every forecast must still receive its own deterministic evaluation, and each evaluation must be associated with its prediction by ID—not by incidental list order. Case acceptance also requires the bounded action path, distinct numeric forecasts, held-out separation, and (in blinded mode) a clean model-facing payload.

The evaluator distinguishes four diagnostic verdicts: `beats_baseline`, `ties_baseline`, `worse_than_baseline`, and `outside_tolerance`. A tie may satisfy the no-worse-than-baseline condition, but it is explicitly **not** evidence of improvement over the baseline.

The initial tolerance is 5% relative error, registered before the held-out value is exposed. This makes a forecast such as 73.4 against a held-out value near 72.6 consistent, while still requiring the same fixed rule for every run.

The benchmark reports, for every prediction:

- held-out value;
- tolerance;
- prediction value;
- deterministic verdict;
- baseline value and error;
- model error;
- whether the forecast beats, ties, or is worse than the baseline.

The benchmark cases are:

- relative atomic mass;
- density;
- melting point, chosen because it is not monotone across the group-14 sequence.

The density and melting-point cases are intentionally harder because the neighbour midpoint is not expected to be as accurate as it is for atomic mass.

### Blinded variant

The ordinary fixture contains historical element labels. The review harness therefore has a blinded mode that replaces those labels with opaque E1-style handles and exposes only the selected property as property_P. The host still retains the real records and the held-out observation.

The blinding check inspects the transformed payload sent to the model, rather than the host's original internal context. It checks complete element-name tokens so ordinary words containing the same letters (for example, "distinct") do not cause false failures. Model-generated statements are still checked for accidental name leakage.

The held-out record is never included in the planner's grounded observations in either mode.

### Competing numeric predictions

A quantitative discriminating prediction is represented as one numeric forecast per competing hypothesis. Presence flags are not part of the historical-rediscovery numeric contract. The host rejects duplicate numeric forecasts because identical numbers do not discriminate between the competing candidates.

An N=20 mode is available through EPISTEME_OLLAMA_RUNS=20. It reports pass rate and prediction spread rather than reducing repeated stochastic runs to a single step-completion PASS.

## What comes next

Only after this benchmark passes should the project generalize the rediscovery machinery to another historical domain such as astronomy, or introduce a concrete observation-acquisition capability for a benchmark that actually requires new observations.

