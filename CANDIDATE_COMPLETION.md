# Episteme Candidate Completion

**Status:** Canonical Phase 10 design  
**Version:** 0.1  
**Last updated:** 2026-09-19

## Purpose

Phase 10 addresses the second half of structural discovery:

> **Given an established structural hole, what could occupy it, and what would make one candidate fit the represented structure better than another without turning fit into a truth score?**

Phase 9 establishes that a bounded structural vacancy exists. Phase 10 may propose candidates for that vacancy.

The central boundary is:

> **The candidate must never be allowed to become evidence merely because it explains the hole.**

Candidate completion is generated reasoning over an established gap and its constraints. It is not observation, measurement, validation, or truth adjudication.

## The Two-Stage Boundary

Episteme must preserve this sequence:

**grounded evidence → structural analysis → established gap → candidate completions → discriminating prediction → experiment/result → evaluation**

Candidate generation must not:

- create the gap it claims to fill;
- alter the gap's structural constraints;
- rewrite grounded inputs to make a candidate fit;
- promote a candidate into evidence;
- suppress competing candidates because one was generated first;
- treat explanatory fit as confirmation.

A candidate may be revised or rejected, but the original gap and prior candidate remain historical artifacts.

## What Is a Candidate?

A candidate is a generated proposed occupant or explanation for an established structural gap.

Depending on the gap type, a candidate may be:

- an entity;
- a relationship;
- a value;
- a mechanism;
- a state;
- a missing component;
- a model or explanatory hypothesis.

The candidate's form is domain-dependent. The epistemic boundary is not.

Every candidate must identify:

- the structural gap it addresses;
- the candidate statement or representation;
- the grounded inputs used;
- the structural constraints inherited from the gap;
- assumptions introduced by the candidate;
- the method and method version;
- the rationale for proposing it.

A candidate is not required to be correct. It is required to be inspectable.

## Candidate and Hypothesis

The existing `Hypothesis` primitive already represents a generated candidate explanation with:

- a stable identifier;
- motivating finding identifiers;
- grounded/integrity input identifiers;
- a statement;
- assumptions;
- method and version;
- rationale;
- reproducibility metadata.

Therefore Phase 10 does not automatically justify creating a second generic candidate primitive.

An initial candidate completion may produce an existing `Hypothesis` when the candidate is explanatory in nature and the established structural gap is one of its motivating findings.

A new primitive is justified only if implementation demonstrates a semantic requirement that `Hypothesis` cannot represent without conflating distinct concepts.

In particular, the **candidate's constraint ledger is not itself a hypothesis**. It records analysis of a candidate against the established gap and must remain distinct from the candidate statement.

## The Constraint Ledger

The first Phase 10 design primitive is an inspectable constraint ledger.

It answers:

> **What happens when this candidate is placed against the constraints that established the hole?**

For each applicable constraint, the ledger should preserve:

- the constraint identity or structural basis;
- whether the candidate satisfies, violates, or leaves the constraint unresolved;
- the evidence or structural context used for that assessment;
- any assumption required by the candidate;
- an explanation of the assessment;
- the method and method version.

The ledger must not collapse these entries into a universal score.

A candidate that satisfies five constraints and violates one is not automatically assigned a numerical fit. The actual constraints and the violation remain visible.

## Constraint Status

The initial semantic vocabulary is deliberately small:

- **satisfied** — the candidate is compatible with the stated constraint under the recorded assumptions;
- **violated** — the candidate conflicts with the stated constraint under the recorded assumptions;
- **unresolved** — the represented knowledge is insufficient to determine compatibility.

An unresolved constraint is not a failure.

A satisfied constraint is not proof.

A violated constraint is not necessarily proof that the candidate is impossible unless the domain-specific rule establishing that consequence is itself explicit.

## Unsupported Assumptions

Candidates may introduce assumptions that were not required to establish the original gap.

These must be visible.

An assumption is unsupported in the Phase 10 sense when the represented candidate completion provides no grounded or explicitly justified basis for requiring it.

The system must distinguish:

- assumptions inherited from the gap or upstream analysis;
- assumptions introduced by the candidate;
- assumptions supported by represented evidence;
- assumptions that remain unsupported.

The existence of an unsupported assumption does not automatically disqualify a candidate. It records an epistemic cost that researchers can inspect.

## Constraint Settlement

The design intuition called **settlement** is retained, but it is not a scalar.

A candidate appears to settle into a structural hole when, under explicit domain rules, it:

- satisfies independently grounded constraints;
- preserves relationships already represented;
- introduces few unsupported assumptions;
- avoids unexplained violations;
- remains compatible with known boundary conditions;
- produces useful, discriminating consequences.

These are separate observations about the candidate.

The system must preserve them as a ledger rather than compute a universal settlement, coherence, elegance, plausibility, or truth number.

The descriptive principle is:

> **Prefer candidates that satisfy more independently grounded constraints while introducing fewer unsupported assumptions, subject to domain-specific rules.**

“Prefer” here describes a future comparison operation. It does not authorize automatic ranking or truth selection.

## Independence

Multiple constraints must not be treated as independent merely because they appear as separate ledger entries.

Independence, when scientifically relevant, must be established from:

- provenance;
- source identity;
- derivation path;
- structural basis;
- domain-specific methodology.

Counting entries is not a substitute for establishing independence.

This follows the Phase 9 structural-pressure rule.

## Violations and Exceptions

A candidate must not be allowed to redefine a constraint merely by violating it.

If a candidate requires an exception, the exception must be represented as an explicit assumption or additional proposal.

The system must preserve:

- the original constraint;
- the candidate's violation;
- the proposed exception, if any;
- the basis for the exception;
- whether the exception is grounded, justified by an explicit rule, or unsupported.

This prevents the completion process from quietly moving the goalposts.

## Competing Candidates

A structural gap may have zero, one, or many candidates.

Episteme must preserve all generated candidates that meet the candidate-generation contract.

It must not collapse alternatives because:

- one was generated first;
- one is simpler by an unspecified criterion;
- one has a model-generated confidence;
- one fits a single observation;
- one feels more elegant.

Comparison is itself an inspectable operation.

When candidates differ, the system should identify which constraints distinguish them.

## The Important Question: What Would Tell Them Apart?

A candidate completion is incomplete when it merely explains the existing structure and no observation could distinguish it from an alternative.

Every viable candidate should therefore expose, where possible:

- predicted consequences;
- conditions under which those consequences apply;
- competing candidate identifiers;
- the observation that would differ;
- assumptions required for the distinction.

This connects Phase 10 directly to the existing prediction and experiment machinery.

The intended progression is:

**gap → candidates → constraint ledger → distinguishing prediction → experiment proposal → grounded result → evaluation**

Phase 10 does not itself make the prediction true.

## Candidate Generation Must Be Downstream

Candidate generation may use:

- the established gap;
- its structural expectation;
- its grounded input identifiers;
- its structural-pressure components;
- related grounded knowledge;
- explicitly permitted external evidence;
- domain-specific rules.

Candidate generation must not use a candidate as evidence for discovering the same gap.

This prevents circular completion:

**candidate → evidence → gap → same candidate**

The dependency must remain one-directional.

## External Evidence

External evidence may be used to propose or assess a candidate when an explicit ingestion or analysis path provides it.

The evidence remains independently grounded.

Candidate generation must record:

- which external evidence was used;
- its provenance;
- how it was transformed;
- what role it played;
- which candidate or constraint assessment consumed it.

A candidate does not inherit the epistemic status of evidence used to generate it.

## Candidate Assessment Is Not Validation

Phase 10 may determine that a candidate is:

- compatible with represented constraints;
- in conflict with represented constraints;
- unresolved under available information.

It must not turn those assessments into a universal declaration that the candidate is true or false.

Domain-specific impossibility rules may eventually establish stronger consequences, but those rules must be explicit and inspectable.

## Immutability and Revision

Candidate completion is historical analysis.

If a candidate is revised:

- the original candidate remains;
- the revised candidate receives a distinct identity;
- the relationship between them is explicit;
- the reason for revision is recorded;
- the evidence or result motivating revision is preserved.

The system must never rewrite an old candidate to match a later result.

## Reproducibility

Candidate completion must be reproducible relative to:

- the established gap;
- the represented grounded state;
- the selected supporting inputs;
- the candidate-generation method and version;
- the structural constraints;
- the candidate's assumptions;
- the schema version.

A change in any of these may legitimately produce a different candidate or assessment.

The generated artifact's fresh identifier is not part of semantic reproduction.

## Deferred Decisions

Phase 10 does not yet define:

- a universal candidate-ranking algorithm;
- a universal plausibility or confidence score;
- a universal definition of simplicity;
- a universal definition of independence;
- autonomous candidate selection;
- automatic truth adjudication;
- universal domain-specific constraint semantics;
- automatic external evidence discovery;
- a mandatory language-model provider.

These require evidence and architectural pressure rather than anticipation.

## Initial Implementation Boundary

The first implementation should prove semantics before optimizing generation.

It should be able to:

1. accept an already established structural gap;
2. generate at least one candidate without modifying that gap;
3. preserve the candidate's assumptions and supporting inputs;
4. record a structured constraint ledger;
5. represent satisfied, violated, and unresolved constraints distinctly;
6. preserve competing candidates without collapsing them;
7. expose at least one discriminating consequence where the represented candidates permit one;
8. reproduce candidate analysis from the same represented state and method;
9. keep every candidate and assessment outside the grounded evidence boundary.

The first implementation should use existing `Hypothesis` and `Prediction` primitives where their semantics fit. New core primitives should be introduced only where a demonstrated semantic mismatch requires them.

## Phase 10 Exit Condition

Phase 10 is complete when Episteme can take an established structural gap and produce inspectable candidate completions that:

- remain downstream of the established gap;
- preserve the gap's structural constraints;
- expose candidate assumptions;
- record constraint-by-constraint assessment without a universal score;
- preserve competing candidates;
- identify discriminating consequences where available;
- remain distinct from grounded evidence;
- are reproducible from their represented inputs and methods.

The implementation and proof boundary for Phase 10 are now complete. The tested path runs from an established structural gap through competing candidates, constraint assessment, discriminating predictions, experiment proposal, grounded result, independent evaluations, and explicit knowledge-state consequences. Renewed discovery can then surface a new tension from differing evaluation outcomes without rewriting the underlying evidence.

The purpose of Phase 10 is not to make Episteme choose an answer.

The purpose is to make possible answers **settle against the structure without hiding the reasons why**.
