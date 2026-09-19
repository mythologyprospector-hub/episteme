# Episteme Structural Gaps

**Status:** Canonical Phase 9 design
**Version:** 0.1
**Last updated:** 2026-09-19

## Purpose

Phase 9 begins the transition from finding explicitly requested absences to finding **structurally meaningful holes** in represented knowledge.

The central question is:

> **When does an absence become informative because the structure around it implies that something should occupy the missing position?**

A structural gap is not a missing database entry. It is a bounded absence exposed by relationships, regularities, constraints, or expectations that are themselves represented and inspectable.

The design is deliberately conservative. Phase 9 does not assume that every elegant pattern in a dataset corresponds to a missing fact in reality.

## Central Rule

> **The hole must be established before the candidate answer is proposed.**

Episteme must first establish:

1. what structure is represented;
2. what regularity, constraint, or expectation creates the vacancy;
3. exactly what is absent;
4. why the vacancy is meaningful within the represented structure;
5. what evidence would distinguish a real external gap from an artifact of incomplete representation.

Only after those steps may later phases search for candidate occupants.

## Structural Gap

A structural gap is a generated discovery finding with all of the following:

- a defined structural context;
- an explicit expectation or constraint derived from that context;
- a bounded missing position, relationship, value, or state;
- traceable grounded inputs supporting the context;
- a reproducible method for deriving the expectation;
- an explicit statement that the absence is relative to the represented knowledge state.

A structural gap does **not** assert that the corresponding object, property, or mechanism exists in external reality.

## Types of Structural Gap

Phase 9 initially recognizes four forms.

### 1. Positional Gap

A represented ordered or classified structure contains an expected position for which no represented occupant exists.

The expectation must come from an explicit structure, not from arbitrary numbering.

### 2. Relational Gap

Multiple represented entities exhibit a reproducible relationship pattern and one bounded relation required by that pattern is absent.

The pattern itself must be represented and traceable.

### 3. Constraint Gap

Represented observations satisfy a constraint across a domain, while a bounded region of the relevant state space remains unrepresented.

The system identifies the missing region without asserting that a real-world state occupies it.

### 4. Accounting Gap

Represented quantities or relationships require an explicit balance, conservation, partition, or accounting structure, but a bounded term remains unresolved.

The accounting rule must be externally grounded or explicitly supplied as an analysis rule.

### Constraint Gap Implementation

The first constraint-gap detector uses an explicit bounded numeric state-space rule.

A caller supplies:

- the grounded records to inspect;
- the numeric payload field;
- a finite lower and upper bound;
- an inspection interval width.

The detector verifies that every supplied observation satisfies the explicit bounds, partitions that bounded region at the declared resolution, and reports only an **interior empty interval with grounded observations in both immediately neighboring intervals**.

This deliberately avoids treating boundary sparsity as a hole. It establishes a vacancy between represented regions inside an explicitly constrained state space.

The detector records the complete constraint and empty interval in a typed constraint expectation. It does not infer that an external state occupies the interval and does not propose a candidate value.

This is an analysis rule, not a universal statement that the underlying domain is continuously populated. The interval width is therefore part of the method's reproducible semantics.


## What Does Not Count

The following are not structural gaps by themselves:

- an empty database field;
- an absent relationship with no expectation;
- a sparse graph;
- a surprising word or phrase;
- a model's request for another parameter;
- a language-model suggestion;
- a low-frequency observation;
- an unexplained phenomenon with no bounded structural context;
- an arbitrary interpolation;
- a missing value inferred solely because it would make a pattern prettier.

An aesthetically pleasing pattern is not evidence of a hole.

## Evidence Boundary

Structural-gap detection operates on represented knowledge and generated structural analysis.

Grounded inputs remain grounded.

The detected gap remains generated.

The expectation that establishes the gap is analysis metadata unless its basis is itself an externally grounded record.

Episteme must preserve the distinction between:

- **grounded fact:** what was observed or reported;
- **structural rule:** what relationship, regularity, or constraint is being applied;
- **gap:** what position or state is absent under that rule;
- **candidate occupant:** a later proposed explanation for the gap.

None of these may silently become another category.

## Hole Before Answer

Phase 9 deliberately separates two problems.

### Problem A — Hole discovery

Determine whether a bounded structural vacancy exists.

### Problem B — Hole completion

Search for candidate explanations, entities, mechanisms, values, or relationships that could occupy the vacancy.

Phase 9 defines Problem A.

Problem B remains a later capability and must not be smuggled into the gap detector.

This separation is essential to the intended Mendeleevian behavior. The system should be able to say:

> “There is a position here that the current structure does not account for.”

without immediately saying:

> “Therefore the missing thing must be X.”

## Structural Pressure

A structural gap may be more compelling when multiple independent constraints point toward the same vacancy.

This is called **structural pressure**.

Structural pressure is not initially a universal numerical score.

Instead, Phase 9 records its components explicitly:

- number of independent grounded constraints;
- diversity of supporting sources;
- number of distinct structural relations converging on the gap;
- whether the vacancy is reproduced under independent representations;
- whether known boundary conditions explain the apparent absence.

The system must retain the components rather than collapse them into a single universal importance value.

### Structural Pressure Ledger

The current representation is an ordered, immutable ledger attached to a gap finding. Each component records:

- a structural component kind;
- a human-readable basis describing the constraint or structural reason;
- the grounded input identifiers on which that component rests;
- the method and method version that produced the component.

Components are serialized as part of the finding, so the ledger is reproducible with the finding's other generated metadata. Multiple components may coexist even when they arise from materially different structural analyses.

The ledger does **not** contain a pressure, confidence, importance, coherence, or truth score. Distinct components remain distinct. Their coexistence records convergent structural reasons without asserting that those reasons are statistically independent or that convergence proves an external-world occupant exists.

Independence, when relevant, is therefore a property to be established by the component's provenance and structural basis, not something inferred from simply counting components.


## Expectation Representation

Phase 9 generalized discovery expectations so the missing thing established by a structural gap is no longer forced into a relationship-shaped tuple.

A discovery expectation is a generated, typed structure with:

- an explicit expectation kind;
- structured data appropriate to that kind;
- deterministic serialization;
- validation at the model boundary;
- compatibility with legacy relationship-shaped expectations when reading existing persisted findings.

The initial expectation kinds are:

- **relationship** — an expected subject/predicate/object connection;
- **positional** — an expected numeric or otherwise explicitly bounded position;
- **constraint** — an expected structural constraint or bounded state condition;
- **accounting** — an expected quantity or accounting term required by an explicit balance structure.

This does not mean that every structural gap must use the expectation kind corresponding to its gap category. The gap describes the form of the vacancy; the expectation describes what the structural analysis says is missing. Keeping those concepts separate prevents the data model from collapsing distinct epistemic questions into one shape.

The expectation remains generated analysis metadata. It does not become grounded evidence merely because its inputs are grounded. Candidate completion remains a separate later operation.

## Candidate Completion — Deferred

A future completion method may examine a structural gap and generate candidate occupants.

Such a method must preserve:

- the gap it attempts to fill;
- every constraint used;
- every assumption introduced;
- the candidate itself;
- the reason the candidate satisfies or violates each constraint;
- the provenance of any external evidence used;
- the method and version.

A candidate is not accepted because it fits one pattern.

The intended completion behavior is **constraint settlement**:

> Prefer candidates that satisfy more independently grounded constraints while introducing fewer unsupported assumptions, subject to domain-specific rules.

This phrase is descriptive, not yet an algorithm or universal score.

## Settlement Must Not Become a Truth Score

Episteme must not introduce a universal scalar called coherence, elegance, fit, energy, plausibility, or settlement and treat it as truth.

Different scientific domains may require different comparison semantics.

The first implementation should therefore preserve a structured constraint ledger rather than inventing a single number.

## Falsification Boundary

Every future candidate-completion method must expose what would distinguish a candidate from its alternatives.

A candidate that merely explains existing structure but makes no testable distinction is not sufficient for scientific completion.

The intended progression is:

**structural gap → candidate completions → constraint comparison → discriminating prediction → experiment/result → evaluation**

## Reproducibility

A structural gap must be reproducible relative to:

- the represented grounded state;
- the structural-analysis method and version;
- the explicit structural rules;
- the selected inputs;
- the schema version.

Changing the underlying knowledge state may change the discovered gap.

Historical generated findings remain immutable and inspectable.

## Phase 9 Exit Condition

Phase 9 is complete when Episteme can:

1. identify bounded structural gaps without relying on arbitrary missing fields;
2. preserve the structural context and constraints that establish each gap;
3. distinguish grounded evidence, structural rules, gaps, and candidate completions;
4. represent structural pressure as inspectable components rather than a universal score;
5. reproduce structural-gap findings from the same represented state and method;
6. demonstrate the method on at least two materially different structures without introducing a domain-specific core primitive.

Phase 9 does not require autonomous candidate completion.

