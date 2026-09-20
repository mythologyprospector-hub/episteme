# Public Acquisition / Capture Inspection

**Status:** Canonical Phase 21 design
**Version:** 1.0
**Last updated:** 2026-09-20

## Goal
Expose persisted external acquisition and captured-representation state through Episteme's existing read-only public scientific instrument.

## Pressure
Episteme can now acquire and preserve an external representation, but a researcher cannot yet directly inspect the persisted capture through the public Python, CLI, and HTTP surfaces.

## Invariant
> **Public inspection may expose acquisition and capture state; it must not turn that state into evidence, interpretation, or authority.**

## Boundary
**persisted captured representation → existing read-only public inspection**

## Inspection Surfaces
Python provides retrieval and deterministic listing with optional source filtering.
CLI provides capture and captures commands.
HTTP provides GET /api/v1/captures and GET /api/v1/captures/{id}.

All surfaces return the existing CapturedRepresentation.to_dict() representation directly.

## Epistemic Boundary
A captured representation records what Episteme received from an external provider. It is not itself a grounded scientific record merely because it is publicly inspectable.

## Determinism and Failure
Listing uses the existing store ordering: captured_at, id. Failed and partial captures remain inspectable. Inspection does not retry, repair, infer, or suppress.

## Out of Scope
New providers, autonomous retrieval, mutation endpoints, interpretation, automatic ingestion, evidence promotion, provenance redesign, workflow integration, ranking, reverse indexes, and content download routes.

## Exit Condition
A researcher can directly retrieve a persisted captured representation and deterministically list captures through Episteme's public Python, CLI, and HTTP surfaces, including source filtering, while preserving the existing capture representation and epistemic boundary.
