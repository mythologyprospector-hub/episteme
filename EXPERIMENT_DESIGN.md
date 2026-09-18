# Episteme Experiment Design

**Status:** Canonical Phase 5 design
**Version:** 0.3
**Last updated:** 2026-09-18
**Phase status:** Complete

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
- discrimination basis explaining why the proposed observation could produce different outcomes under the predictions being tested;
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

A proposal must state the basis for its expected discrimination without assigning a single canonical ranking. The discrimination basis explains the expected difference in observable outcomes between the predictions being tested; it is explanatory metadata, not a score.

Phase 5 must preserve the hypotheses and predictions that motivate the proposed test.

## Results

A result is an externally grounded record representing what was actually observed or measured.

A result must be independently ingested with appropriate provenance and explicitly related to the experiment proposal and predictions it tests.

A proposal must never be rewritten to match its later result.

## Uncertainty and Scope

Phase 5 represents the reason a proposed observation is expected to reduce uncertainty through its explicit discrimination basis. This is contextual explanatory metadata, not a universal confidence or quality score.

A general uncertainty-tracking calculus is intentionally outside this phase.

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
