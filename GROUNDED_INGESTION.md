# Episteme Grounded Evidence Ingestion

**Status:** Complete — Canonical Phase 11 design
**Version:** 0.1
**Last updated:** 2026-09-19

## Purpose

Phase 11 strengthens the boundary through which externally supplied scientific material enters Episteme.

The goal is not autonomous web discovery. The goal is to make the existing ingestion boundary capable of accepting heterogeneous, finite source representations while preserving exactly what came from the source, how Episteme represented it, and what Episteme later inferred.

The governing chain is:

**external source representation → source-specific adapter → canonical grounded record → ordinary Episteme validation/persistence**

When translation itself is scientifically or operationally important, its reproducible transformation must also remain inspectable:

**source record → translation operation → canonical output record**

## Core Invariant

**Ingestion may translate representation; it may not manufacture epistemic authority.**

An adapter may normalize syntax, preserve source fields, identify source state, and produce canonical records. It may not turn source interpretation into independently observed evidence, silently repair missing information, or infer claims merely because a source format makes them convenient to extract.

## Existing Boundary

Episteme already has two relevant entry points:

- canonical UTF-8 JSON Lines ingestion through the existing JSONL adapter;
- a finite Crossref work-metadata adapter.

These establish the basic external-source-to-grounded-record pattern. Phase 11 therefore does not introduce a second ingestion object model.

The phase instead tests and hardens the boundary that already exists.

## Source State

An imported source must preserve, where available:

- stable source identity;
- source location;
- source version, revision, publication timestamp, or equivalent source-state marker;
- Episteme capture timestamp;
- source-provided content relevant to the represented record.

A content digest may be used when a source representation lacks a stronger version identifier, but a digest identifies a representation; it does not establish scientific correctness.

## Translation Provenance

The ingestion boundary distinguishes two questions:

1. **Where did this material originate?**
2. **How did Episteme translate it?**

Source provenance answers the first.

When translation is material to reproducibility, an existing Transformation records the second using its input records, operation and version, assumptions, outputs, execution timestamp, validation result, and provenance.

No new universal ingestion provenance primitive is required unless implementation demonstrates that the existing provenance and transformation primitives cannot represent the needed boundary cleanly.

## Determinism

For a fixed finite source representation and fixed adapter version, translation must be deterministic.

Determinism means repeated translation of the same represented input produces the same represented content and stable identity rules where the adapter defines them. It does not mean repeated ingestion must be silently deduplicated.

Immutable records remain immutable. Re-importing a source must never overwrite an existing record.

## Heterogeneous Material

A source may contain multiple epistemic kinds.

An adapter must preserve distinctions that are explicit in the source. In particular:

- source metadata remains source material;
- observations remain observations when the source actually identifies them as such;
- measurements remain measurements when represented as such;
- source-authored interpretations do not become independent observations merely because they are stated confidently;
- unsupported material is retained as source material or explicitly rejected rather than silently promoted.

Phase 11 does not attempt universal semantic extraction. Domain-specific extraction remains above the stable core.

## Rejection

Malformed or unsupported material must fail explicitly.

The ingestion boundary must not:

- invent missing provenance;
- silently repair malformed values;
- silently discard unsupported source material;
- infer scientific claims from metadata alone;
- overwrite immutable records;
- use semantic similarity as an implicit deduplication rule.

Batch adapters should validate the complete batch before persistence when practical, so a partially accepted source cannot masquerade as a complete import.

## Scope

Phase 11 begins with finite, caller-supplied source representations.

It does not include:

- autonomous web crawling;
- source ranking or credibility scoring;
- authentication management;
- universal document parsing;
- autonomous claim extraction;
- model-provider requirements;
- laboratory control;
- web-scale scheduling.

Those may become later architectural questions only if actual use demonstrates the need.

## Exit Condition

Phase 11 is complete when Episteme can:

1. accept at least two materially different finite external source representations;
2. preserve source and capture provenance;
3. preserve source-provided content without silently changing its epistemic meaning;
4. translate deterministically under a named adapter and version;
5. explicitly reject malformed or unsupported material;
6. preserve immutable records across re-import;
7. keep generated interpretation outside the grounded evidence boundary;
8. demonstrate the boundary with executable tests and inspectable provenance/translation lineage.

The phase is not complete merely because another importer exists. The exit condition is the preservation of epistemic distinctions under heterogeneous ingestion.
