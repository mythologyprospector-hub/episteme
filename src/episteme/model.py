"""Core Phase 1 knowledge records.

This module contains the smallest domain model required by the grounded
knowledge substrate. It deliberately avoids persistence, frameworks, and
external services.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping
from uuid import UUID, uuid4
import json


SCHEMA_VERSION = 1


class RecordKind(StrEnum):
    SOURCE = "source"
    OBSERVATION = "observation"
    MEASUREMENT = "measurement"
    DATASET = "dataset"
    EXPERIMENT = "experiment"
    RESULT = "result"


def _require_text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")


def _require_uuid(value: str, field: str) -> None:
    _require_text(value, field)
    try:
        UUID(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be a UUID string") from exc


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
        _require_text(self.captured_at, "captured_at")
        for value, field in (
            (self.source_location, "source_location"),
            (self.source_version, "source_version"),
            (self.note, "note"),
        ):
            if value is not None and not isinstance(value, str):
                raise ValueError(f"{field} must be a string or None")

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
