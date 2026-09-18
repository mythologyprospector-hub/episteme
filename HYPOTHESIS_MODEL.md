# Episteme Hypothesis Model

**Status:** Canonical Phase 4 design  
**Version:** 0.1  
**Last updated:** 2026-09-18

## Purpose

Phase 4 turns supported discovery findings into candidate explanations and testable predictions without promoting those explanations to grounded knowledge.

The central rule is:

> **A hypothesis is a proposed explanation, not evidence for itself.**

Phase 4 therefore makes the relationship between evidence, discovery, hypothesis, assumptions, and predictions explicit.

## Epistemic Boundary

Phase 4 operates above the grounded substrate, integrity layer, and discovery layer.

The dependency direction is:

**Grounded Knowledge → Integrity → Discovery Findings → Hypotheses / Models → Predictions**

Hypotheses and predictions are generated structures. They must remain distinguishable from grounded records.

A hypothesis may use discovery findings as reasoning inputs, but those findings remain derived artifacts. The hypothesis does not inherit their epistemic status.

## Hypothesis

A hypothesis is a candidate explanation proposed to account for one or more supported findings.

A hypothesis must preserve:

- stable identifier;
- human-readable statement;
- ordered input finding identifiers;
- ordered grounded/integrity input identifiers when directly used;
- method and method version;
- rationale;
- assumptions;
- creation timestamp;
- schema version.

The required inputs establish why the hypothesis was proposed. They do not establish that the hypothesis is true.

### Hypothesis Requirements

A valid hypothesis must:

1. identify what it proposes to explain;
2. identify the findings or evidence motivating it;
3. preserve its assumptions;
4. remain explicitly generated;
5. avoid claiming external truth;
6. be reproducible from its recorded inputs and method where practical.

A hypothesis may be wrong. Being wrong is an acceptable state; silently converting it into evidence is not.

## Models

A model is a structured representation of an explanatory mechanism or system.

Phase 4 does not require a universal scientific modeling language.

A model may initially remain generic and preserve domain-specific structure without forcing a universal ontology.

Models must point to the hypotheses or grounded material from which their structure was derived.

Model generation is not the same as model validation.

## Assumptions

Assumptions are first-class parts of a hypothesis or model.

An assumption records what the proposed explanation requires to be treated as true, fixed, ignored, approximate, or otherwise constrained for the proposal to operate.

Assumptions must remain inspectable.

Changing an assumption changes the explanatory proposal and should produce a distinct hypothesis/model state rather than silently rewriting the previous proposal.

Phase 4 does not assign a universal confidence score to assumptions.

## Predictions

A prediction is a testable consequence derived from a hypothesis or model.

A prediction must preserve:

- stable identifier;
- source hypothesis or model identifier;
- human-readable predicted consequence;
- conditions or scope;
- ordered assumptions used;
- method and method version;
- rationale;
- creation timestamp;
- schema version.

A prediction is not a measurement.

It becomes externally grounded only when an observation, measurement, experiment, or result is independently ingested and explicitly related to it.

## Competing Explanations

Phase 4 must permit multiple hypotheses to address the same finding.

The system must not collapse competing explanations into one preferred explanation merely because one was generated first, appears simpler, or receives a model-generated score.

Competing hypotheses should share the finding or evidence they attempt to explain while remaining separate proposals.

The comparison question is:

> **What observable consequence would differ between these explanations?**

This prepares the architecture for Phase 5 experiment design.

## Distinguishing Consequences

The Phase 4 exit condition requires candidate explanations whose distinguishing consequences are explicit.

A distinguishing consequence is a prediction or predicted outcome whose result would differ between two or more competing hypotheses under stated conditions.

Phase 4 records the consequence. Phase 5 determines how to efficiently obtain the observation that discriminates among the alternatives.

## Provenance and Reproducibility

Generated hypotheses and predictions preserve:

- upstream identifiers;
- method and version;
- rationale;
- assumptions;
- timestamps;
- schema version.

This records the generation path.

It does not certify the proposal.

If an external model or language model assists generation, that model is a tool. Its output is still a generated hypothesis or prediction until independently supported.

## Failure and Revision

A prediction that later fails is valuable information.

Phase 4 must not rewrite the original prediction to match a later result.

A new interpretation or revised hypothesis should be represented separately and connected explicitly to the prior proposal and the result that motivated revision.

## Deferred Decisions

Phase 4 intentionally does not define:

- universal model semantics;
- domain-specific mathematical representations;
- confidence or truth scores for hypotheses;
- autonomous hypothesis selection;
- automatic model canonization;
- language-model provider;
- automatic hypothesis ranking;
- experiment optimization.

These require additional evidence and architectural decisions.

## Phase 4 Exit Condition

Phase 4 is complete when Episteme can:

1. represent candidate hypotheses as generated explanations;
2. preserve the findings/evidence motivating each hypothesis;
3. represent assumptions explicitly;
4. generate bounded predictions from hypotheses;
5. represent multiple competing explanations without collapsing them;
6. make distinguishing consequences explicit;
7. keep hypotheses and predictions separate from grounded evidence.

The purpose of Phase 4 is not to make Episteme believe a hypothesis.

The purpose is to make a hypothesis **testable**.
