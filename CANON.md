# Episteme Canon

**Status:** Canonical  
**Version:** 0.2  
**Last updated:** 2026-09-18

## Purpose

Episteme is an open scientific discovery engine intended to help humanity turn knowledge into better knowledge.

It maps what is known, what is claimed, what is supported, what is uncertain, what is contradictory, what has not been measured, and what experiments could distinguish competing explanations.

Episteme is not intended to manufacture certainty. Its purpose is to make the boundary between knowledge and unknowns more explicit and more useful.

## Governing Principles

### 1. Evidence precedes interpretation

Observations, measurements, datasets, experimental results, and source records must remain distinguishable from claims, models, hypotheses, analogies, and inferences.

A generated interpretation does not become a fact merely because the system generated it.

### 2. Provenance is part of knowledge

A meaningful scientific statement must retain enough provenance to answer:

- Where did it come from?
- What was actually observed or reported?
- What transformation produced the current representation?
- What assumptions were introduced?
- What supports or contradicts it?

Loss of provenance is loss of epistemic value.

### 3. Unknowns are first-class

Episteme must represent unresolved, unmeasured, contradictory, insufficiently evidenced, and unexplored states explicitly.

An empty space is not automatically a discovery. A gap becomes interesting when its existence and significance are independently grounded.

### 4. The system must not discover its own footprints

A concept, relationship, gap, or hypothesis introduced solely by Episteme must not be treated as independent evidence for a discovery.

The system must preserve the distinction between externally grounded knowledge and internally generated structure.

### 5. Contradictions are valuable

Contradictory observations, incompatible models, failed predictions, and unresolved disputes are not noise to be silently removed.

They are signals that may identify where better evidence or better models are needed.

### 6. Prefer discriminating experiments

When multiple explanations remain viable, Episteme should seek observations or experiments that distinguish among them.

Generating another plausible explanation is less useful than finding a way to tell existing explanations apart.

### 7. Failure is information

A failed prediction or unsuccessful experiment is an epistemic result.

Results must be recorded rather than rewritten to preserve a preferred hypothesis.

### 8. No silent canonization

Generated claims, inferred relationships, hypotheses, and proposed structures do not silently become canonical facts.

Transitions in epistemic status must be explicit, traceable, and governed.

### 9. Reproducibility matters

A discovery path should be inspectable.

Where practical, Episteme should preserve the inputs, transformations, assumptions, evidence, outputs, and validation results needed to reproduce or challenge a conclusion.

### 10. Uncertainty must survive the pipeline

Uncertainty may be reduced by evidence, but it must not disappear merely because data passed through a cleaner representation, model, prompt, or interface.

### 11. The machine serves inquiry

Episteme is an instrument for investigation, not an authority over truth.

Human researchers and external evidence remain capable of challenging the system.

### 12. Architecture follows epistemology

The software structure must preserve the distinctions above.

Convenience must not collapse distinctions that matter scientifically.

## Epistemic Boundary

Episteme maintains three broad domains:

1. **Grounded world** — observations, measurements, datasets, source records, experiments, and results.
2. **Interpretive world** — claims, models, hypotheses, predictions, analogies, and inferences.
3. **Unknown world** — unresolved, unmeasured, contradictory, insufficiently evidenced, and unexplored states.

These domains may be connected, but they must not be conflated.

## Canonization Rule

A design or architectural decision becomes canonical when it is deliberately recorded in the repository's governing documentation.

Implementation must conform to canon.

If implementation reveals that canon is inadequate, the correct sequence is:

**identify → discuss → revise canon → implement → verify**

not:

**implement → rationalize later**

## Scope Boundary

Episteme is an independent project.

Existing system infrastructure may be studied as an integration reference, but Episteme must not silently modify or absorb unrelated repositories.

The abandoned discovery project examined during planning is historical archaeology only. Its implementation and architectural choices are not inherited by Episteme unless independently re-established here.

## Change Discipline

Before introducing a new architectural concept:

1. Search the repository for an existing concept or document serving that purpose.
2. Reuse or extend an existing source of truth when appropriate.
3. Determine whether the proposed concept changes the canonical architecture.
4. Record the decision before relying on it in implementation.
5. Update affected documentation and tests together.

## What Canon Means Here

Canon describes commitments the project intends to preserve.

It does not claim that the implementation is complete, that every scientific assumption is correct, or that future evidence cannot require revision.

When canon changes, the change should be visible in version history.

### 13. Discovery outputs are not evidence

Episteme may generate gaps, tensions, questions, hypotheses, and other structures while analyzing knowledge.

Generated structures remain generated.

A discovery finding may identify where evidence is incomplete or in conflict, but its existence does not establish an external fact. Discovery methods must preserve the grounded inputs and reasoning path that produced the finding.

### 14. Absence is not automatically a discovery

A missing relationship, field, measurement, or document is not by itself evidence that the corresponding scientific fact is unknown, false, or important.

Episteme may identify a gap only relative to an explicit expectation or grounded context, and it must preserve the basis for that expectation.
