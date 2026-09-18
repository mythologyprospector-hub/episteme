# Episteme Discovery Model

**Status:** Canonical Phase 3 design
**Version:** 0.2
**Last updated:** 2026-09-18

## Purpose

This document defines the minimum discovery semantics for Phase 3.

Discovery is the act of finding useful structure in the knowledge substrate without promoting that structure to externally grounded knowledge.

The central rule is:

> **Discovery may reveal a gap in knowledge without pretending to know what fills it.**

## Finding Kinds

### Gap

A bounded absence or unresolved state relative to an explicit expectation or grounded context.

A graph being sparse is not enough.

### Tension

Grounded material that creates an unresolved conflict, incompatibility, or competing state under an explicit comparison rule.

### Contradiction

An explicit or reproducibly detected incompatibility between represented material.

Phase 3 begins with explicit `contradicts` relationships.

### Unresolved Question

A bounded question generated from a gap or tension.

A question is not an answer and is not evidence.

## What Makes a Finding Meaningful

A Phase 3 finding must satisfy all of the following:

1. **Bounded** — the finding identifies a specific missing, conflicting, or unresolved element.
2. **Traceable** — the finding names the records that caused it to exist.
3. **Methodical** — the discovery method and version are recorded.
4. **Reproducible** — another execution of the same method against the same inputs can explain the same finding.
5. **Non-self-supporting** — generated findings cannot serve as independent evidence for themselves.
6. **Epistemically modest** — the finding states what was detected, not what has been proven beyond its inputs.

## Gap Detection

Phase 3 does not treat every absent edge as a gap.

Gap detection requires an explicit expectation. The expectation may come from:

- a grounded scientific context represented in the substrate; or
- an explicit analysis request supplied to the discovery engine.

The discovery engine evaluates the expectation against the current grounded state.

For example, an analysis request may ask whether a particular subject has a particular relationship to a particular object. If the requested relationship is absent, the engine may produce a **candidate gap**.

The expectation is preserved with the finding as a structured subject, predicate, and object. This keeps the exact request inspectable rather than reconstructing it from generated prose.

The candidate gap means:

> “This expected item is not represented in the inspected knowledge state.”

It does **not** mean:

> “The item does not exist in the external world.”

## Expectation Traceability

An expectation is part of the discovery input for gap detection, not evidence about the external world. A gap finding preserves the exact expected subject, predicate, and object so that the discovery operation can be reproduced and audited. The absence of the expected relationship remains a property of the inspected knowledge state only.

## Contradiction Discovery

Phase 3 first uses explicit contradiction structure.

A `contradicts` relationship is already a grounded relationship and can therefore be surfaced as a discovery signal without inventing semantics.

Two records having different payloads is not sufficient to declare a contradiction.

Future semantic contradiction detectors may compare values, units, scope, time, methods, and other domain semantics, but those rules require their own documented basis and tests.

## Question Generation

Questions are generated from accepted gaps or tensions.

A generated question must preserve:

- the finding that produced it;
- the grounded inputs behind that finding;
- the discovery method;
- the exact unresolved subject;
- the exact expectation when the source finding is an expectation-based gap.

For an expectation-based gap, the unresolved question carries the same structured subject, predicate, and object expectation. This preserves the original analysis request without turning the request into evidence.

Question generation must not silently fill the missing value.

## Significance

Phase 3 treats significance as an attention problem, not a truth problem.

A finding may carry several named measures. Examples include:

- evidence breadth;
- source diversity;
- conflict density;
- coverage deficit;
- downstream dependency count.

Measures are method-specific and must retain enough metadata to explain what the number means.

Phase 3 does not define a universal significance score.

## Deferred Discovery

The following are explicitly deferred:

- semantic contradiction inference;
- autonomous ontology completion;
- language-model-dependent discovery;
- learned novelty scores;
- universal importance rankings;
- automatic conversion of findings into hypotheses.

Those capabilities may become appropriate later, but they require additional epistemic design.

## Phase 3 Exit Condition

Phase 3 is complete when Episteme can:

1. inspect grounded knowledge;
2. produce traceable gap findings and surface explicit contradiction structure;
3. generate bounded unresolved questions;
4. record reproducible discovery methods;
5. attach interpretable significance measures;
6. keep all generated material distinguishable from grounded evidence.

Semantic tension detection is not required for the Phase 3 exit condition; its rules remain deferred until a reproducible comparison basis can be defined.


## Renewed Discovery — Phase 6

Phase 6 renews discovery after experimental results have entered the knowledge state.

Prediction evaluations and knowledge-state consequences are generated context. They may describe how results bear on predictions and interpretive targets, but they are not evidence and must never be treated as grounded inputs.

A renewed discovery finding therefore keeps two lineages separate:

- `input_ids` — grounded or integrity-layer evidence that supports the finding;
- `context_ids` — generated evaluations and knowledge-state consequences inspected while producing the finding.

### Evaluation-Conflict Detection

The first renewed-discovery method is deliberately conservative: it detects when the same prediction has been evaluated with different outcome classifications under the same recorded comparison conditions and assumptions.

The method:

1. groups prediction evaluations by prediction identifier, comparison conditions, and assumptions;
2. requires at least two evaluations in a group;
3. requires more than one outcome classification in that group;
4. produces a bounded **tension** finding;
5. places the evaluated grounded result identifiers in `input_ids`;
6. places the prediction evaluation identifiers in `context_ids`;
7. records the comparison rule and method version in the finding rationale.

The method does not decide which evaluation is correct, whether the prediction is true or false, or whether the differing outcomes are caused by an error. It only identifies a represented state in which the same prediction has received differing classifications under matching recorded comparison context.

Knowledge-state consequences may be inspected alongside evaluations in later renewed-discovery methods, but they are not evidence. A consequence conflict must not be inferred until its comparison rule is separately documented.

This first method intentionally does not assign a ranking, confidence score, or universal significance score.

### Reproducibility Boundary

Renewed discovery is reproducible only relative to the represented evaluation state and the method version. If later evidence adds another evaluation, the discovery result may change because the inspected knowledge state changed. Earlier findings remain inspectable as historical generated artifacts.



## Reproducible Discovery Trails — Phase 6

A discovery trail reconstructs the represented lineage behind a generated discovery finding without creating a new epistemic object.

The first trail begins at a renewed discovery finding and follows explicit references backward through generated evaluation context and grounded results to the prediction, experiment proposal when represented, hypothesis/model, motivating discovery finding, and grounded/integrity inputs.

The trail is read-only and preserves object identifiers and categories. It never treats generated material as evidence and never infers a missing connection.

The trail has a full serialized form and a reproducible lineage form. The full form includes the trail creation timestamp. The lineage form excludes that generation metadata, so the same repository state, starting finding identifier, and trail-method version produce the same canonical lineage representation regardless of when the trail was reconstructed. Both forms contain ordered traversal entries, object kinds and identifiers, the explicit reference used at each step, method/version, and schema version.

Missing optional references are represented as absent. Missing required lineage fails explicitly.

This is a reconstruction/report boundary, not a new persistence layer or discovery algorithm.
