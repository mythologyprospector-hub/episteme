# Episteme

> An open scientific discovery engine for mapping knowledge, exposing unknowns, testing hypotheses, and finding the experiments that matter.

![Episteme social preview](assets/episteme-social-preview.jpg)

## What Is Episteme?

Episteme is an open project exploring whether a machine can help humanity discover things we do not yet know.

It is designed to keep several things separate that are too often blended together:

- evidence
- observations
- claims
- models
- hypotheses
- predictions
- contradictions
- unknowns
- experiments
- results

The goal is not to make a machine that sounds certain.

The goal is to build an instrument that can show **why we believe something, where the gaps are, what competing explanations remain possible, and what evidence would help distinguish them.**

## The Core Idea

Episteme follows a closed discovery loop:

**evidence → knowledge → gaps → hypotheses → predictions → experiments → results → new knowledge**

The loop matters because discovery should not stop at generating plausible ideas.

A useful discovery system must eventually be able to ask:

> **What could we observe next that would actually tell us something?**

## Principles

The project is governed by [CANON.md](CANON.md).

The central architectural invariant is:

> **No information may gain epistemic authority merely by passing through Episteme.**

That means an AI-generated hypothesis remains a hypothesis until independently supported. A failed experiment remains a result. A contradiction remains visible. An unknown remains an unknown.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the canonical system design.

The architecture separates:

- the **grounded world** — externally sourced observations, measurements, datasets, experiments, and results;
- the **interpretive world** — claims, models, hypotheses, predictions, analogies, and inferences;
- the **unknown world** — unresolved, unmeasured, contradictory, insufficiently evidenced, and unexplored states.

Phase 1 has a small executable grounded knowledge substrate with deterministic serialization, structural provenance checks, first-class relationships, and SQLite persistence.

## Roadmap

See [ROADMAP.md](ROADMAP.md).

Development begins with the smallest trustworthy knowledge substrate rather than with a large autonomous reasoning system.

## Documentation

Documentation follows the project's [Documentation Standard](DOCUMENTATION_STYLE.md).

The first documents to read are:

1. [Canon](CANON.md)
2. [Architecture](ARCHITECTURE.md)
3. [Roadmap](ROADMAP.md)
4. [Contributing](CONTRIBUTING.md)

## Project Status

**Current phase:** Phase 15 — Artifact-to-Execution Lineage

Phase 1 grounded substrate, Phase 2 knowledge integrity, and Phase 3 discovery are complete and verified. Phase 4 hypothesis and prediction, Phase 5 experiment design, and Phase 6 closed-loop discovery are also complete and verified.

Phase 7 is complete and verified. The first two domain demonstrations are Astronomy and Biology, showing that materially different evidence shapes can use domain-specific layers while preserving Episteme's stable epistemic primitives, provenance, generated-versus-grounded boundaries, closed-loop lineage, and reproducibility.

Phase 8 established the public scientific instrument and is complete. Phase 9 established structural-gap discovery and is complete. Phase 10 established candidate completion downstream of those gaps and is complete. Phase 11 established the grounded evidence ingestion boundary and is complete. Phase 12 is complete. Phase 13 established durable execution history and is complete. Phase 14 exposed that durable execution history through the existing read-only public instrument and is complete. Phase 15 established reverse artifact-to-execution lineage and is complete. The canonical Phase 13 design is documented in [EXECUTION_HISTORY.md](EXECUTION_HISTORY.md), the Phase 14 design in [PUBLIC_EXECUTION_TRACEABILITY.md](PUBLIC_EXECUTION_TRACEABILITY.md), and the Phase 15 design in [ARTIFACT_EXECUTION_LINEAGE.md](ARTIFACT_EXECUTION_LINEAGE.md).

## Project Boundary

Episteme is an independent project.

Existing system infrastructure may provide integration reference material, but unrelated repositories are outside Episteme's working scope.

Historical experiments and abandoned implementations are treated as archaeology, not inherited architecture.

## Author

**James Earl Stambaugh III**  
GitHub: [@mythologyprospector-hub](https://github.com/mythologyprospector-hub)  
Email: mythologyprospector@gmail.com

## License

License selection is intentionally not fixed yet.
