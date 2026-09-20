"""Read-only public inspection API for Episteme."""

from __future__ import annotations

from typing import Any

from .model import ReviewTargetKind
from .orchestration import WorkflowDefinition, WorkflowExecution
from .store import Store
from .trail import build_discovery_trail


class PublicNotFoundError(ValueError):
    """A requested public resource does not exist."""



def get_record(store: Store, record_id: str) -> dict[str, Any]:
    """Return one grounded record as a canonical public representation."""
    record = store.get_record(record_id)
    if record is None:
        raise PublicNotFoundError(f"record not found: {record_id}")
    return record.to_dict()


def list_records(store: Store, kind: str | None = None) -> list[dict[str, Any]]:
    """Return grounded records in the store's deterministic order."""
    return [record.to_dict() for record in store.iter_records(kind=kind)]



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
    "get_record",
    "list_records",
    "get_review",
    "list_reviews",
    "get_workflow_definition",
    "list_workflow_definitions",
    "get_workflow_execution",
    "list_workflow_executions",
    "workflow_execution_lineage",
    "discovery_trail",
    "discovery_lineage",
    "discovery_report",
]
