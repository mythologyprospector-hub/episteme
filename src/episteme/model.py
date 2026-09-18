"""Core knowledge records.

This module contains the domain model required by the grounded knowledge
substrate and its integrity layer. It deliberately avoids persistence,
frameworks, and external services.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from datetime import datetime
import json
from typing import Any, Mapping
from urllib.parse import urlparse
from uuid import UUID, uuid4


SCHEMA_VERSION = 1


class RecordKind(StrEnum):
    SOURCE = "source"
    OBSERVATION = "observation"
    MEASUREMENT = "measurement"
    DATASET = "dataset"
    EXPERIMENT = "experiment"
    RESULT = "result"


class LifecycleEventKind(StrEnum):
    CREATED = "created"
    SUPERSEDED = "superseded"
    RETRACTED = "retracted"


class AssessmentTargetKind(StrEnum):
    RECORD = "record"
    RELATIONSHIP = "relationship"


def _require_text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")


def _require_uuid(value: str, field: str) -> None:
    _require_text(value, field)
    try:
        UUID(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be a UUID string") from exc


def _require_iso_timestamp(value: str, field: str) -> None:
    _require_text(value, field)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO-8601/RFC-3339 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone")


def _require_absolute_uri(value: str, field: str) -> None:
    _require_text(value, field)
    parsed = urlparse(value)
    if not parsed.scheme:
        raise ValueError(f"{field} must be an absolute URI")


def canonical_json(value: Any) -> str:
    """Return deterministic JSON for values accepted by the substrate."""

    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("value must be JSON-compatible") from exc


@dataclass(frozen=True, slots=True)
class Provenance:
    """Where a grounded record came from."""

    source_id: str
    captured_at: str
    source_location: str | None = None
    source_version: str | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.source_id, "source_id")
        _require_iso_timestamp(self.captured_at, "captured_at")
        if self.source_location is not None:
            _require_absolute_uri(self.source_location, "source_location")
        if self.source_version is not None:
            _require_text(self.source_version, "source_version")
        if self.note is not None:
            _require_text(self.note, "note")

    def to_dict(self) -> dict[str, str]:
        data: dict[str, str] = {
            "source_id": self.source_id,
            "captured_at": self.captured_at,
        }
        if self.source_location is not None:
            data["source_location"] = self.source_location
        if self.source_version is not None:
            data["source_version"] = self.source_version
        if self.note is not None:
            data["note"] = self.note
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Provenance":
        return cls(
            source_id=data["source_id"],
            captured_at=data["captured_at"],
            source_location=data.get("source_location"),
            source_version=data.get("source_version"),
            note=data.get("note"),
        )


@dataclass(frozen=True, slots=True)
class Record:
    """A grounded knowledge record."""

    id: str
    kind: RecordKind
    payload: Mapping[str, Any]
    provenance: tuple[Provenance, ...]
    created_at: str
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_uuid(self.id, "id")
        if not isinstance(self.kind, RecordKind):
            raise ValueError("kind must be a RecordKind")
        if not isinstance(self.payload, Mapping):
            raise ValueError("payload must be a mapping")
        if not self.provenance:
            raise ValueError("record requires at least one provenance entry")
        _require_text(self.created_at, "created_at")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version: {self.schema_version}")
        canonical_json(dict(self.payload))
        for entry in self.provenance:
            if not isinstance(entry, Provenance):
                raise ValueError("provenance entries must be Provenance objects")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind.value,
            "payload": dict(self.payload),
            "provenance": [entry.to_dict() for entry in self.provenance],
            "created_at": self.created_at,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Record":
        return cls(
            id=data["id"],
            kind=RecordKind(data["kind"]),
            payload=data["payload"],
            provenance=tuple(Provenance.from_dict(item) for item in data["provenance"]),
            created_at=data["created_at"],
            schema_version=data.get("schema_version", SCHEMA_VERSION),
        )


@dataclass(frozen=True, slots=True)
class Relationship:
    """A first-class relationship between two grounded records."""

    id: str
    subject_id: str
    predicate: str
    object_id: str
    provenance: tuple[Provenance, ...]
    created_at: str
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_uuid(self.id, "id")
        _require_uuid(self.subject_id, "subject_id")
        _require_text(self.predicate, "predicate")
        _require_uuid(self.object_id, "object_id")
        if not self.provenance:
            raise ValueError("relationship requires at least one provenance entry")
        _require_text(self.created_at, "created_at")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version: {self.schema_version}")
        for entry in self.provenance:
            if not isinstance(entry, Provenance):
                raise ValueError("provenance entries must be Provenance objects")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "subject_id": self.subject_id,
            "predicate": self.predicate,
            "object_id": self.object_id,
            "provenance": [entry.to_dict() for entry in self.provenance],
            "created_at": self.created_at,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Relationship":
        return cls(
            id=data["id"],
            subject_id=data["subject_id"],
            predicate=data["predicate"],
            object_id=data["object_id"],
            provenance=tuple(Provenance.from_dict(item) for item in data["provenance"]),
            created_at=data["created_at"],
            schema_version=data.get("schema_version", SCHEMA_VERSION),
        )


@dataclass(frozen=True, slots=True)
class LifecycleEvent:
    """An append-only lifecycle change for an existing record."""

    id: str
    record_id: str
    kind: LifecycleEventKind
    occurred_at: str
    provenance: tuple[Provenance, ...]
    replacement_record_id: str | None = None
    reason: str | None = None
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_uuid(self.id, "id")
        _require_uuid(self.record_id, "record_id")
        if not isinstance(self.kind, LifecycleEventKind):
            raise ValueError("kind must be a LifecycleEventKind")
        _require_text(self.occurred_at, "occurred_at")
        if not self.provenance:
            raise ValueError("lifecycle event requires provenance")
        if self.replacement_record_id is not None:
            _require_uuid(self.replacement_record_id, "replacement_record_id")
        if self.reason is not None:
            _require_text(self.reason, "reason")
        if self.kind is LifecycleEventKind.SUPERSEDED and self.replacement_record_id is None:
            raise ValueError("superseded event requires replacement_record_id")
        if self.kind is LifecycleEventKind.RETRACTED and self.reason is None:
            raise ValueError("retracted event requires reason")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version: {self.schema_version}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "record_id": self.record_id,
            "kind": self.kind.value,
            "occurred_at": self.occurred_at,
            "provenance": [item.to_dict() for item in self.provenance],
            "replacement_record_id": self.replacement_record_id,
            "reason": self.reason,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "LifecycleEvent":
        return cls(
            id=data["id"],
            record_id=data["record_id"],
            kind=LifecycleEventKind(data["kind"]),
            occurred_at=data["occurred_at"],
            provenance=tuple(Provenance.from_dict(item) for item in data["provenance"]),
            replacement_record_id=data.get("replacement_record_id"),
            reason=data.get("reason"),
            schema_version=data.get("schema_version", SCHEMA_VERSION),
        )


@dataclass(frozen=True, slots=True)
class EvidenceAssessment:
    """A contextual assessment of evidence, not a truth score."""

    id: str
    target_kind: AssessmentTargetKind
    target_id: str
    method: str
    basis: str
    rationale: str
    provenance: tuple[Provenance, ...]
    assessed_at: str
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_uuid(self.id, "id")
        if not isinstance(self.target_kind, AssessmentTargetKind):
            raise ValueError("target_kind must be an AssessmentTargetKind")
        _require_uuid(self.target_id, "target_id")
        _require_text(self.method, "method")
        _require_text(self.basis, "basis")
        _require_text(self.rationale, "rationale")
        _require_text(self.assessed_at, "assessed_at")
        if not self.provenance:
            raise ValueError("assessment requires provenance")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version: {self.schema_version}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "target_kind": self.target_kind.value,
            "target_id": self.target_id,
            "method": self.method,
            "basis": self.basis,
            "rationale": self.rationale,
            "provenance": [item.to_dict() for item in self.provenance],
            "assessed_at": self.assessed_at,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "EvidenceAssessment":
        return cls(
            id=data["id"],
            target_kind=AssessmentTargetKind(data["target_kind"]),
            target_id=data["target_id"],
            method=data["method"],
            basis=data["basis"],
            rationale=data["rationale"],
            provenance=tuple(Provenance.from_dict(item) for item in data["provenance"]),
            assessed_at=data["assessed_at"],
            schema_version=data.get("schema_version", SCHEMA_VERSION),
        )


@dataclass(frozen=True, slots=True)
class Transformation:
    """A reproducible relationship between existing records."""

    id: str
    input_ids: tuple[str, ...]
    operation: str
    operation_version: str
    assumptions: tuple[str, ...]
    output_ids: tuple[str, ...]
    executed_at: str
    validation_result: str
    provenance: tuple[Provenance, ...]
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_uuid(self.id, "id")
        if not self.input_ids:
            raise ValueError("transformation requires at least one input")
        if not self.output_ids:
            raise ValueError("transformation requires at least one output")
        for record_id in (*self.input_ids, *self.output_ids):
            _require_uuid(record_id, "record_id")
        _require_text(self.operation, "operation")
        _require_text(self.operation_version, "operation_version")
        _require_text(self.executed_at, "executed_at")
        _require_text(self.validation_result, "validation_result")
        if not self.provenance:
            raise ValueError("transformation requires provenance")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version: {self.schema_version}")
        for assumption in self.assumptions:
            _require_text(assumption, "assumption")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "input_ids": list(self.input_ids),
            "operation": self.operation,
            "operation_version": self.operation_version,
            "assumptions": list(self.assumptions),
            "output_ids": list(self.output_ids),
            "executed_at": self.executed_at,
            "validation_result": self.validation_result,
            "provenance": [item.to_dict() for item in self.provenance],
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Transformation":
        return cls(
            id=data["id"],
            input_ids=tuple(data["input_ids"]),
            operation=data["operation"],
            operation_version=data["operation_version"],
            assumptions=tuple(data["assumptions"]),
            output_ids=tuple(data["output_ids"]),
            executed_at=data["executed_at"],
            validation_result=data["validation_result"],
            provenance=tuple(Provenance.from_dict(item) for item in data["provenance"]),
            schema_version=data.get("schema_version", SCHEMA_VERSION),
        )


def make_record(
    kind: RecordKind,
    payload: Mapping[str, Any],
    provenance: tuple[Provenance, ...],
    created_at: str,
) -> Record:
    """Create a new grounded record with a fresh UUID."""

    return Record(
        id=str(uuid4()),
        kind=kind,
        payload=payload,
        provenance=provenance,
        created_at=created_at,
    )


def make_relationship(
    subject_id: str,
    predicate: str,
    object_id: str,
    provenance: tuple[Provenance, ...],
    created_at: str,
) -> Relationship:
    """Create a new grounded relationship with a fresh UUID."""

    return Relationship(
        id=str(uuid4()),
        subject_id=subject_id,
        predicate=predicate,
        object_id=object_id,
        provenance=provenance,
        created_at=created_at,
    )
