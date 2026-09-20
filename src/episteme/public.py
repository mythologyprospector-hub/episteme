"""Read-only public inspection API for Episteme."""

from __future__ import annotations

from typing import Any

from .model import ReviewTargetKind
from .orchestration import WorkflowDefinition, WorkflowExecution
from .store import Store
from .trail import build_discovery_trail


class PublicNotFoundError(ValueError):
    """A requested public resource does not exist."""



def get_captured_representation(store: Store, capture_id: str) -> dict[str, Any]:
    """Return one captured external representation as a public representation."""
    capture = store.get_captured_representation(capture_id)
    if capture is None:
        raise PublicNotFoundError(f"captured representation not found: {capture_id}")
    return capture.to_dict()


def list_captured_representations(store: Store, source_id: str | None = None) -> list[dict[str, Any]]:
    """Return captured representations in deterministic order."""
    return [capture.to_dict() for capture in store.iter_captured_representations(source_id=source_id)]


def get_captured_content(store: Store, capture_id: str) -> tuple[bytes, str]:
    """Return the exact persisted captured bytes and their media type."""
    capture = store.get_captured_representation(capture_id)
    if capture is None:
        raise PublicNotFoundError(f"captured representation not found: {capture_id}")
    if capture.content_reference is None:
        raise PublicNotFoundError(f"captured representation has no content: {capture_id}")
    try:
        content = store.read_captured_content(capture_id)
    except ValueError as exc:
        raise PublicNotFoundError(str(exc)) from exc
    return content, capture.media_type or "application/octet-stream"


def get_record(store: Store, record_id: str) -> dict[str, Any]:
    """Return one grounded record as a canonical public representation."""
    record = store.get_record(record_id)
    if record is None:
        raise PublicNotFoundError(f"record not found: {record_id}")
    return record.to_dict()


def list_records(store: Store, kind: str | None = None) -> list[dict[str, Any]]:
    """Return grounded records in the store's deterministic order."""
    return [record.to_dict() for record in store.iter_records(kind=kind)]



def get_relationship(store: Store, relationship_id: str) -> dict[str, Any]:
    """Return one grounded relationship as a public representation."""
    relationship = store.get_relationship(relationship_id)
    if relationship is None:
        raise PublicNotFoundError(f"relationship not found: {relationship_id}")
    return relationship.to_dict()


def list_relationships(
    store: Store, predicate: str | None = None
) -> list[dict[str, Any]]:
    """Return grounded relationships in deterministic order."""
    return [
        relationship.to_dict()
        for relationship in store.iter_relationships(predicate=predicate)
    ]


def get_review(store: Store, review_id: str) -> dict[str, Any]:
    """Return one immutable review as a public representation."""
    review = store.get_review(review_id)
    if review is None:
        raise PublicNotFoundError(f"review not found: {review_id}")
    return review.to_dict()


def list_reviews(
    store: Store,
    target_kind: ReviewTargetKind | None = None,
    target_id: str | None = None,
) -> list[dict[str, Any]]:
    """Return reviews in deterministic order, optionally scoped to a target."""
    return [
        review.to_dict()
        for review in store.iter_reviews(target_kind=target_kind, target_id=target_id)
    ]

def get_workflow_definition(store: Store, workflow_id: str) -> dict[str, Any]:
    """Return one persisted workflow definition as a public representation."""
    workflow = store.get_workflow_definition(workflow_id)
    if workflow is None:
        raise PublicNotFoundError(f"workflow definition not found: {workflow_id}")
    return workflow.to_dict()


def list_workflow_definitions(store: Store) -> list[dict[str, Any]]:
    """Return persisted workflow definitions in deterministic order."""
    return [workflow.to_dict() for workflow in store.iter_workflow_definitions()]


def get_workflow_execution(store: Store, execution_id: str) -> dict[str, Any]:
    """Return one persisted workflow execution as a public representation."""
    execution = store.get_workflow_execution(execution_id)
    if execution is None:
        raise PublicNotFoundError(f"workflow execution not found: {execution_id}")
    return execution.to_dict()


def list_workflow_executions(
    store: Store, workflow_id: str | None = None
) -> list[dict[str, Any]]:
    """Return persisted workflow executions in deterministic order."""
    return [
        execution.to_dict()
        for execution in store.iter_workflow_executions(workflow_id=workflow_id)
    ]


def workflow_execution_lineage(store: Store, execution_id: str) -> dict[str, Any]:
    """Return timestamp-independent lineage for one persisted execution."""
    execution = store.get_workflow_execution(execution_id)
    if execution is None:
        raise PublicNotFoundError(f"workflow execution not found: {execution_id}")
    return execution.lineage_dict()


def list_workflow_executions_for_capture(
    store: Store, capture_id: str
) -> list[dict[str, Any]]:
    """Return persisted workflow executions that consumed or produced a capture."""
    capture = store.get_captured_representation(capture_id)
    if capture is None:
        raise PublicNotFoundError(f"captured representation not found: {capture_id}")
    return [
        execution.to_dict()
        for execution in store.iter_workflow_executions_for_artifact(capture_id)
    ]


def list_workflow_executions_for_artifact(
    store: Store, artifact_id: str
) -> list[dict[str, Any]]:
    """Return persisted workflow executions that consumed or produced an artifact."""
    if not store.workflow_artifact_exists(artifact_id):
        raise PublicNotFoundError(f"artifact not found: {artifact_id}")
    return [
        execution.to_dict()
        for execution in store.iter_workflow_executions_for_artifact(artifact_id)
    ]



def get_discovery_finding(store: Store, finding_id: str) -> dict[str, Any]:
    """Return one generated discovery finding as a public representation."""
    finding = store.get_discovery_finding(finding_id)
    if finding is None:
        raise PublicNotFoundError(f"discovery finding not found: {finding_id}")
    return finding.to_dict()


def list_discovery_findings(
    store: Store, kind: str | None = None
) -> list[dict[str, Any]]:
    """Return generated discovery findings in deterministic order."""
    return [
        finding.to_dict()
        for finding in store.iter_discovery_findings(kind=kind)
    ]


def get_hypothesis(store: Store, hypothesis_id: str) -> dict[str, Any]:
    hypothesis = store.get_hypothesis(hypothesis_id)
    if hypothesis is None:
        raise PublicNotFoundError(f"hypothesis not found: {hypothesis_id}")
    return hypothesis.to_dict()


def list_hypotheses(store: Store) -> list[dict[str, Any]]:
    return [item.to_dict() for item in store.iter_hypotheses()]


def get_model(store: Store, model_id: str) -> dict[str, Any]:
    model = store.get_model(model_id)
    if model is None:
        raise PublicNotFoundError(f"model not found: {model_id}")
    return model.to_dict()


def list_models(store: Store) -> list[dict[str, Any]]:
    return [item.to_dict() for item in store.iter_models()]


def get_prediction(store: Store, prediction_id: str) -> dict[str, Any]:
    prediction = store.get_prediction(prediction_id)
    if prediction is None:
        raise PublicNotFoundError(f"prediction not found: {prediction_id}")
    return prediction.to_dict()


def list_predictions(store: Store) -> list[dict[str, Any]]:
    return [item.to_dict() for item in store.iter_predictions()]


def get_experiment_proposal(store: Store, proposal_id: str) -> dict[str, Any]:
    proposal = store.get_experiment_proposal(proposal_id)
    if proposal is None:
        raise PublicNotFoundError(f"experiment proposal not found: {proposal_id}")
    return proposal.to_dict()


def list_experiment_proposals(store: Store) -> list[dict[str, Any]]:
    return [item.to_dict() for item in store.iter_experiment_proposals()]


def get_prediction_evaluation(store: Store, evaluation_id: str) -> dict[str, Any]:
    evaluation = store.get_prediction_evaluation(evaluation_id)
    if evaluation is None:
        raise PublicNotFoundError(f"prediction evaluation not found: {evaluation_id}")
    return evaluation.to_dict()


def list_prediction_evaluations(store: Store) -> list[dict[str, Any]]:
    return [item.to_dict() for item in store.iter_prediction_evaluations()]


def get_knowledge_state_consequence(store: Store, consequence_id: str) -> dict[str, Any]:
    consequence = store.get_knowledge_state_consequence(consequence_id)
    if consequence is None:
        raise PublicNotFoundError(
            f"knowledge-state consequence not found: {consequence_id}"
        )
    return consequence.to_dict()


def list_knowledge_state_consequences(store: Store) -> list[dict[str, Any]]:
    return [item.to_dict() for item in store.iter_knowledge_state_consequences()]

def discovery_trail(
    store: Store,
    finding_id: str,
    created_at: str,
) -> dict[str, Any]:
    """Reconstruct one discovery trail without modifying repository state."""
    return build_discovery_trail(store, finding_id, created_at).to_dict()


def discovery_lineage(
    store: Store,
    finding_id: str,
    created_at: str,
) -> dict[str, Any]:
    """Return the timestamp-independent canonical lineage representation."""
    return build_discovery_trail(store, finding_id, created_at).to_lineage_dict()


def discovery_report(
    store: Store,
    finding_id: str,
    created_at: str,
) -> dict[str, Any]:
    """Return an inspectable report assembled from existing Episteme state."""
    trail = build_discovery_trail(store, finding_id, created_at)
    grounded = [
        entry.to_dict()
        for entry in trail.entries
        if entry.kind in {"record", "relationship"}
    ]
    generated = [
        entry.to_dict()
        for entry in trail.entries
        if entry.kind not in {"record", "relationship"}
    ]
    return {
        "report": "episteme-discovery-report-v1",
        "finding_id": finding_id,
        "grounded_records": grounded,
        "generated_artifacts": generated,
        "trail": trail.to_dict(),
        "lineage": trail.to_lineage_dict(),
    }


__all__ = [
    "PublicNotFoundError",
    "get_captured_representation",
    "list_captured_representations",
    "get_captured_content",
    "get_record",
    "list_records",
    "get_discovery_finding",
    "list_discovery_findings",
    "get_hypothesis",
    "list_hypotheses",
    "get_model",
    "list_models",
    "get_prediction",
    "list_predictions",
    "get_experiment_proposal",
    "list_experiment_proposals",
    "get_prediction_evaluation",
    "list_prediction_evaluations",
    "get_knowledge_state_consequence",
    "list_knowledge_state_consequences",
    "get_review",
    "list_reviews",
    "get_relationship",
    "list_relationships",
    "get_workflow_definition",
    "list_workflow_definitions",
    "get_workflow_execution",
    "list_workflow_executions",
    "workflow_execution_lineage",
    "list_workflow_executions_for_artifact",
    "discovery_trail",
    "discovery_lineage",
    "discovery_report",
]
