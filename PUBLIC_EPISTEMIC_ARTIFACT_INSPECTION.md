# Phase 17 — Public Epistemic Artifact Inspection

## Goal

Expose existing generated epistemic artifacts through Episteme's existing read-only public scientific instrument without changing their epistemic status.

## Architectural Pressure

Episteme already persists first-class generated artifacts used by hypothesis formation, model construction, prediction, experiment design, prediction evaluation, and knowledge-state consequence tracking. These artifacts participate in discovery trails, reviews, and workflow execution history.

The public instrument can expose surrounding history, but it does not yet provide a canonical direct inspection surface for each persisted generated artifact.

This is a public-inspection gap, not a missing epistemic primitive.

## Governing Invariant

> **Public epistemic-artifact inspection may expose a generated artifact and its existing lineage; it may not make that artifact grounded merely because it is publicly inspectable.**

## Boundary

The Phase 17 boundary is:

**persisted generated epistemic artifact → public Python API → read-only CLI / HTTP**

The implementation reuses the existing model serialization and Store persistence boundary. No second representation is introduced.

## Artifact Types

Phase 17 exposes the existing persisted generated artifact types:

- Hypothesis
- Model
- Prediction
- ExperimentProposal
- PredictionEvaluation
- KnowledgeStateConsequence

These are generated/contextual artifacts, not grounded evidence.

## Public Python Surface

The public API provides deterministic retrieval and listing for each artifact type:

- get_hypothesis / list_hypotheses
- get_model / list_models
- get_prediction / list_predictions
- get_experiment_proposal / list_experiment_proposals
- get_prediction_evaluation / list_prediction_evaluations
- get_knowledge_state_consequence / list_knowledge_state_consequences

Each representation is the existing model's to_dict() result.

## CLI Surface

The installed episteme command provides read-only inspection:

- hypotheses
- hypothesis <id>
- models
- model <id>
- predictions
- prediction <id>
- experiment-proposals
- experiment-proposal <id>
- prediction-evaluations
- prediction-evaluation <id>
- knowledge-state-consequences
- knowledge-state-consequence <id>

## HTTP Surface

Versioned read-only routes under /api/v1 provide the same representations:

- GET /api/v1/hypotheses
- GET /api/v1/hypotheses/{id}
- GET /api/v1/models
- GET /api/v1/models/{id}
- GET /api/v1/predictions
- GET /api/v1/predictions/{id}
- GET /api/v1/experiment-proposals
- GET /api/v1/experiment-proposals/{id}
- GET /api/v1/prediction-evaluations
- GET /api/v1/prediction-evaluations/{id}
- GET /api/v1/knowledge-state-consequences
- GET /api/v1/knowledge-state-consequences/{id}

No query filters are introduced in this phase unless an existing Store capability makes one necessary for the canonical surface.

## Semantics

- Retrieval returns the persisted artifact exactly through its existing serializer.
- Listing follows the existing deterministic Store ordering.
- Missing artifacts use the existing public PublicNotFoundError semantics.
- Public inspection is read-only.
- Generated artifacts remain generated.
- Existing artifact lineage fields remain descriptive lineage, not evidence.
- Execution history and discovery trails remain complementary inspection paths rather than being folded into artifact serialization.

## Scope

Phase 17 includes:

- direct read-only Python retrieval and listing;
- read-only CLI inspection;
- read-only versioned HTTP inspection;
- deterministic serialization and ordering;
- missing-resource semantics;
- executable tests;
- synchronized canonical documentation.

## Out of Scope

Phase 17 does not introduce:

- new artifact types;
- new provenance models;
- a second graph or store;
- reverse indexes;
- inference;
- scoring or ranking;
- truth adjudication;
- promotion of generated artifacts to grounded evidence;
- automatic validation;
- mutation through the public surfaces;
- authentication;
- scheduling or distributed execution;
- autonomous agents;
- a mandatory frontend;
- changes to the epistemic meaning of existing artifacts.

## Relationship to Earlier Phases

Phase 14 exposes workflow definitions and executions.

Phase 15 provides reverse lookup from an artifact to executions that consumed or produced it.

Phase 16 exposes first-class relationships directly.

Phase 17 complements those surfaces by allowing a researcher to inspect the generated artifact itself rather than only the surrounding trail, review, relationship, or execution history.

These remain separate because each answers a different inspection question.

## Exit Condition

A researcher using Episteme's documented public inspection surfaces can directly retrieve and list each existing generated epistemic artifact type, inspect its stored content and lineage fields, and distinguish it from grounded evidence without creating a second artifact model or changing its epistemic status.

## Exit Audit

The implemented Phase 17 behavior satisfies the stated exit condition.

- all six existing generated artifact types are directly retrievable and listable through the public Python API;
- the CLI provides read-only retrieval and listing for each artifact type;
- versioned `/api/v1` HTTP routes expose the same existing model representations;
- deterministic Store ordering and existing public missing-resource semantics are preserved;
- generated artifact content and lineage fields remain the existing persisted representations;
- no second artifact model, provenance model, graph, score, inference layer, or mutation surface was introduced;
- the grounded/generated boundary remains unchanged: public inspection does not promote hypotheses, models, predictions, experiment proposals, prediction evaluations, or knowledge-state consequences into grounded evidence;
- executable Phase 17 tests cover the public artifact boundary, including retrieval/listing, missing-resource behavior, CLI inspection, and HTTP inspection;
- GitHub Actions Test run #461 for commit `7fedf34a9bcc5bc551e668489a08c88d31eac4b1` completed successfully.

**Status:** Complete.
