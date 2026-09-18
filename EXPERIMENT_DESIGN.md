# Episteme Experiment Design

**Status:** Canonical Phase 5 design
**Version:** 0.1
**Last updated:** 2026-09-18

## Purpose

Phase 5 turns distinguishing predictions into proposed ways of obtaining observations that can discriminate among competing explanations.

The central rule is:

> **An experiment proposal is a plan for obtaining evidence, not evidence itself.**

## Epistemic Boundary

The dependency direction is:

**Grounded Knowledge → Integrity → Discovery Findings → Hypotheses / Models → Predictions → Experiment Proposals → Results**

An experiment proposal is generated planning material. It does not become a grounded record merely because it is well reasoned or derived from a prediction.

## Experiment Proposal

An experiment proposal should preserve:

- stable identifier;
- ordered prediction identifiers being tested;
- human-readable objective;
- proposed observation or measurement;
- conditions or scope;
- assumptions;
- method and method version;
- rationale;
- creation timestamp;
- schema version.

The proposal describes what could be done or observed. It does not claim that the proposed test has been performed.

## Discriminating Power

Phase 5 asks whether a proposed observation could produce different outcomes under competing explanations.

Discriminating power is contextual, not a universal truth or quality score.

A proposal may state the basis for its expected discrimination without assigning a single canonical ranking.

Phase 5 must preserve the hypotheses and predictions that motivate the proposed test.

## Results

A result is an externally grounded record representing what was actually observed or measured.

A result must be independently ingested with appropriate provenance and explicitly related to the experiment proposal and predictions it tests.

A proposal must never be rewritten to match its later result.

## Uncertainty

Phase 5 may represent uncertainty associated with an experiment proposal when its meaning and basis are explicit.

It must not collapse uncertainty into a universal confidence score for hypotheses.

## Deferred Decisions

Phase 5 does not yet define:

- automatic experiment optimization;
- universal statistical semantics;
- autonomous laboratory control;
- instrument/provider protocols;
- automatic hypothesis selection;
- a universal uncertainty calculus.

## Phase 5 Exit Condition

Phase 5 is complete when Episteme can identify why a proposed observation would reduce uncertainty between competing explanations while preserving the distinction between prediction, proposed test, and observed result.
