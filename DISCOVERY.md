# Episteme Discovery Model

**Status:** Canonical Phase 3 design
**Version:** 0.1
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
- the exact unresolved subject.

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
2. produce traceable gap and tension findings;
3. generate bounded unresolved questions;
4. record reproducible discovery methods;
5. attach interpretable significance measures;
6. keep all generated material distinguishable from grounded evidence.
