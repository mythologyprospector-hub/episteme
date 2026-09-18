# Contributing to Episteme

**Status:** Canonical project guidance  
**Version:** 0.1  
**Last updated:** 2026-09-18

## Purpose

Episteme is built to preserve epistemic clarity as the system grows.

Contributions should therefore improve capability without weakening the distinctions established by [CANON.md](CANON.md).

## Before Changing the Project

1. Read [CANON.md](CANON.md).
2. Read [ARCHITECTURE.md](ARCHITECTURE.md).
3. Check [ROADMAP.md](ROADMAP.md) for the current phase.
4. Search the repository for an existing document, concept, or component that already serves the intended purpose.
5. Determine whether the change introduces or alters an architectural concept.

Do not begin implementation by assuming a missing structure should simply be invented.

## Documentation Before Architecture

When a change introduces a new architectural concept:

1. identify the responsibility and invariant it protects;
2. update the authoritative documentation;
3. review the dependency and boundary implications;
4. implement the concept;
5. add or update verification;
6. update status and roadmap information when appropriate.

The intended sequence is:

**identify → discuss → document → implement → verify**

## Source of Truth

Each concept should have one authoritative home.

Prefer extending an existing document or module over creating another parallel source of truth.

Do not duplicate architectural definitions across multiple documents.

## Epistemic Discipline

Changes must preserve the distinction between:

- externally grounded evidence;
- interpretation and inference;
- unknown or unresolved states.

Generated material must not acquire epistemic authority merely because it passed through an Episteme component.

## Scope Boundary

Episteme is an independent repository.

External infrastructure may be used as an integration reference. Changes to unrelated repositories are outside the working scope unless explicitly requested.

Historical or abandoned projects are reference material only and do not become architecture by implication.

## Verification

A change is not complete merely because it exists.

Where applicable, contributors should provide:

- tests for behavior;
- checks for invariants;
- provenance coverage;
- documentation updates;
- reproducible evidence for important claims.

Use precise status language from [DOCUMENTATION_STYLE.md](DOCUMENTATION_STYLE.md).

## Pull Requests

Pull requests should make the intended change easy to inspect.

A useful pull request explains:

- what changed;
- why it changed;
- which documented decision governs it;
- how it was verified;
- whether canon, architecture, or roadmap changed.

Small coherent changes are preferred over unrelated batches.

## When the Architecture Is Wrong

If implementation exposes a flaw in the documented architecture, do not silently work around it.

Stop at the boundary, document the problem, revise the authoritative decision, then continue.

> **We would rather change the architecture deliberately than accumulate accidental architecture.**
