"""Read-only public inspection API for Episteme."""

from __future__ import annotations

from typing import Any

from .store import Store
from .trail import build_discovery_trail


def get_record(store: Store, record_id: str) -> dict[str, Any]:
    """Return one grounded record as a canonical public representation."""
    record = store.get_record(record_id)
    if record is None:
        raise ValueError(f"record not found: {record_id}")
    return record.to_dict()


def list_records(store: Store, kind: str | None = None) -> list[dict[str, Any]]:
    """Return grounded records in the store's deterministic order."""
    return [record.to_dict() for record in store.iter_records(kind=kind)]


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
        if entry.kind == "record"
    ]
    generated = [
        entry.to_dict()
        for entry in trail.entries
        if entry.kind != "record"
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
    "get_record",
    "list_records",
    "discovery_trail",
    "discovery_lineage",
    "discovery_report",
]
