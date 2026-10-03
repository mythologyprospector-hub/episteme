"""Import boundary for explicit Praxis evidence handoff packets.

The adapter intentionally accepts only the JSON-compatible handoff representation.
It does not import Praxis or infer epistemic meaning from the handoff.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import uuid4

from .model import Provenance, Record, RecordKind
from .store import Store


PRAXIS_HANDOFF_FORMAT = "praxis-evidence-handoff"
PRAXIS_HANDOFF_ADAPTER = "praxis-evidence-handoff"
PRAXIS_HANDOFF_ADAPTER_VERSION = "1"


def import_praxis_evidence_handoff(
    data: Mapping[str, Any],
    store: Store,
) -> Record:
    """Translate one explicit Praxis handoff packet into an Episteme record."""
    if not isinstance(data, Mapping):
        raise ValueError("Praxis handoff must be a mapping")

    schema_version = data.get("schema_version")
    if schema_version != 1:
        raise ValueError("Praxis handoff schema_version must be 1")

    record_kind_value = data.get("record_kind")
    if not isinstance(record_kind_value, str) or not record_kind_value.strip():
        raise ValueError("Praxis handoff requires record_kind")
    try:
        record_kind = RecordKind(record_kind_value)
    except ValueError as exc:
        raise ValueError(
            f"Praxis handoff record_kind is not an Episteme RecordKind: {record_kind_value}"
        ) from exc

    source_id = data.get("source_id")
    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("Praxis handoff requires source_id")

    captured_at = data.get("captured_at")
    if not isinstance(captured_at, str) or not captured_at.strip():
        raise ValueError("Praxis handoff requires captured_at")

    evidence = data.get("praxis_evidence")
    admission = data.get("praxis_admission")
    if not isinstance(evidence, Mapping):
        raise ValueError("Praxis handoff requires praxis_evidence")
    if not isinstance(admission, Mapping):
        raise ValueError("Praxis handoff requires praxis_admission")

    evidence_id = evidence.get("id")
    if not isinstance(evidence_id, str) or not evidence_id.strip():
        raise ValueError("Praxis handoff praxis_evidence requires id")

    admission_evidence_item_id = admission.get("evidence_item_id")
    if admission_evidence_item_id != evidence_id:
        raise ValueError(
            "Praxis handoff admission evidence_item_id must match praxis_evidence id"
        )

    source_location = data.get("source_location")
    if source_location is not None and (
        not isinstance(source_location, str) or not source_location.strip()
    ):
        raise ValueError("Praxis handoff source_location must be a non-empty string")

    provenance = (
        Provenance(
            source_id=source_id,
            captured_at=captured_at,
            source_location=source_location,
            note=f"Imported from {PRAXIS_HANDOFF_FORMAT} v{PRAXIS_HANDOFF_ADAPTER_VERSION}",
        ),
    )

    record = Record(
        id=str(uuid4()),
        kind=record_kind,
        payload={
            "external_format": PRAXIS_HANDOFF_FORMAT,
            "adapter": PRAXIS_HANDOFF_ADAPTER,
            "adapter_version": PRAXIS_HANDOFF_ADAPTER_VERSION,
            "praxis_evidence": dict(evidence),
            "praxis_admission": dict(admission),
        },
        provenance=provenance,
        created_at=captured_at,
    )
    store.put_record(record)
    return record
