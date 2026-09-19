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
import math
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


class PredictionEvaluationOutcome(StrEnum):
    CONSISTENT = "consistent"
    INCONSISTENT = "inconsistent"
    INCONCLUSIVE = "inconclusive"


class AssessmentTargetKind(StrEnum):
    RECORD = "record"
    RELATIONSHIP = "relationship"


class ReviewTargetKind(StrEnum):
    RECORD = "record"
    RELATIONSHIP = "relationship"
    DISCOVERY_FINDING = "discovery_finding"
    HYPOTHESIS = "hypothesis"
    MODEL = "model"
    PREDICTION = "prediction"
    EXPERIMENT_PROPOSAL = "experiment_proposal"
    PREDICTION_EVALUATION = "prediction_evaluation"
    KNOWLEDGE_STATE_CONSEQUENCE = "knowledge_state_consequence"


class ReviewDisposition(StrEnum):
    NOTE = "note"
    QUESTION = "question"
    CHALLENGE = "challenge"
    ACKNOWLEDGE = "acknowledge"


class DiscoveryFindingKind(StrEnum):
    GAP = "gap"
    TENSION = "tension"
    CONTRADICTION = "contradiction"
    UNRESOLVED_QUESTION = "unresolved_question"


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
    """A first-class provenance-bearing relationship between Episteme objects."""

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
class Review:
    """An immutable human or review-process examination of represented material."""

    id: str
    target_kind: ReviewTargetKind
    target_id: str
    reviewer: str
    disposition: ReviewDisposition
    basis: str
    rationale: str
    provenance: tuple[Provenance, ...]
    reviewed_at: str
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_uuid(self.id, "id")
        if not isinstance(self.target_kind, ReviewTargetKind):
            raise ValueError("target_kind must be a ReviewTargetKind")
        _require_uuid(self.target_id, "target_id")
        _require_text(self.reviewer, "reviewer")
        if not isinstance(self.disposition, ReviewDisposition):
            raise ValueError("disposition must be a ReviewDisposition")
        _require_text(self.basis, "basis")        _require_text(self.rationale, "rationale")
        if not self.provenance:
            raise ValueError("review requires provenance")
        _require_iso_timestamp(self.reviewed_at, "reviewed_at")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version: {self.schema_version}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "target_kind": self.target_kind.value,
            "target_id": self.target_id,
            "reviewer": self.reviewer,
            "disposition": self.disposition.value,
            "basis": self.basis,
            "rationale": self.rationale,
            "provenance": [item.to_dict() for item in self.provenance],
            "reviewed_at": self.reviewed_at,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Review":
        return cls(
            id=data["id"],
            target_kind=ReviewTargetKind(data["target_kind"]),
            target_id=data["target_id"],
            reviewer=data["reviewer"],
            disposition=ReviewDisposition(data["disposition"]),
            basis=data["basis"],
            rationale=data["rationale"],
            provenance=tuple(Provenance.from_dict(item) for item in data["provenance"]),
            reviewed_at=data["reviewed_at"],
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


class KnowledgeStateTargetKind(StrEnum):
    HYPOTHESIS = "hypothesis"
    MODEL = "model"
    PREDICTION = "prediction"


class KnowledgeStateConsequenceKind(StrEnum):
    SUPPORTS = "supports"
    WEAKENS = "weakens"
    CONTRADICTS = "contradicts"
    LEAVES_UNRESOLVED = "leaves_unresolved"


@dataclass(frozen=True, slots=True)
class KnowledgeStateConsequence:
    """A generated contextual consequence derived from prediction evaluations."""

    id: str
    evaluation_ids: tuple[str, ...]
    target_kind: KnowledgeStateTargetKind
    target_id: str
    consequence: KnowledgeStateConsequenceKind
    assumptions: tuple[str, ...]
    rationale: str
    method: str
    method_version: str
    created_at: str
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_uuid(self.id, "id")
        if not self.evaluation_ids:
            raise ValueError("knowledge-state consequence requires at least one evaluation")
        for evaluation_id in self.evaluation_ids:
            _require_uuid(evaluation_id, "evaluation_id")
        if not isinstance(self.target_kind, KnowledgeStateTargetKind):
            raise ValueError("target_kind must be a KnowledgeStateTargetKind")
        _require_uuid(self.target_id, "target_id")
        if not isinstance(self.consequence, KnowledgeStateConsequenceKind):
            raise ValueError("consequence must be a KnowledgeStateConsequenceKind")
        for assumption in self.assumptions:
            _require_text(assumption, "assumption")
        _require_text(self.rationale, "rationale")
        _require_text(self.method, "method")
        _require_text(self.method_version, "method_version")
        _require_iso_timestamp(self.created_at, "created_at")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version: {self.schema_version}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "evaluation_ids": list(self.evaluation_ids),
            "target_kind": self.target_kind.value,
            "target_id": self.target_id,
            "consequence": self.consequence.value,
            "assumptions": list(self.assumptions),
            "rationale": self.rationale,
            "method": self.method,
            "method_version": self.method_version,
            "created_at": self.created_at,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "KnowledgeStateConsequence":
        return cls(
            id=data["id"],
            evaluation_ids=tuple(data["evaluation_ids"]),
            target_kind=KnowledgeStateTargetKind(data["target_kind"]),
            target_id=data["target_id"],
            consequence=KnowledgeStateConsequenceKind(data["consequence"]),
            assumptions=tuple(data["assumptions"]),
            rationale=data["rationale"],
            method=data["method"],
            method_version=data["method_version"],
            created_at=data["created_at"],
            schema_version=data.get("schema_version", SCHEMA_VERSION),
        )


@dataclass(frozen=True, slots=True)
class DiscoveryMeasure:
    """A named discovery signal; not a universal truth or confidence score."""

    name: str
    value: float
    scale: str
    basis: str

    def __post_init__(self) -> None:
        _require_text(self.name, "name")
        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
            raise ValueError("value must be a number")
        if not math.isfinite(float(self.value)):
            raise ValueError("value must be finite")
        _require_text(self.scale, "scale")
        _require_text(self.basis, "basis")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "scale": self.scale,
            "basis": self.basis,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DiscoveryMeasure":
        return cls(
            name=data["name"],
            value=data["value"],
            scale=data["scale"],
            basis=data["basis"],
        )


class DiscoveryExpectationKind(StrEnum):
    """The structural kind of thing a discovery finding expects to be represented."""

    RELATIONSHIP = "relationship"
    POSITIONAL = "positional"
    CONSTRAINT = "constraint"
    ACCOUNTING = "accounting"


@dataclass(frozen=True, slots=True)
class DiscoveryExpectation:
    """A typed, inspectable expectation; never a claim that the expected thing exists."""

    kind: DiscoveryExpectationKind
    data: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.kind, DiscoveryExpectationKind):
            raise ValueError("kind must be a DiscoveryExpectationKind")
        if not isinstance(self.data, Mapping):
            raise ValueError("data must be a mapping")
        canonical_json(dict(self.data))

        if self.kind is DiscoveryExpectationKind.RELATIONSHIP:
            required = ("subject_id", "predicate", "object_id")
            if set(self.data) != set(required):
                raise ValueError("relationship expectation data must contain exactly subject_id, predicate, and object_id")
            _require_uuid(self.data["subject_id"], "expectation subject_id")
            _require_text(self.data["predicate"], "expectation predicate")
            _require_uuid(self.data["object_id"], "expectation object_id")
        elif self.kind is DiscoveryExpectationKind.POSITIONAL:
            if "position" not in self.data:
                raise ValueError("positional expectation requires position")
            if isinstance(self.data["position"], bool) or not isinstance(self.data["position"], (int, float)):
                raise ValueError("positional expectation position must be numeric")
        elif self.kind is DiscoveryExpectationKind.CONSTRAINT:
            _require_text(self.data.get("constraint"), "expectation constraint")
        elif self.kind is DiscoveryExpectationKind.ACCOUNTING:
            _require_text(self.data.get("quantity"), "expectation quantity")

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind.value, "data": dict(self.data)}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DiscoveryExpectation":
        return cls(kind=DiscoveryExpectationKind(data["kind"]), data=data["data"])


@dataclass(frozen=True, slots=True)
class DiscoveryFinding:
    """A generated discovery artifact derived from grounded inputs."""

    id: str
    kind: DiscoveryFindingKind
    title: str
    description: str
    input_ids: tuple[str, ...]
    method: str
    method_version: str
    rationale: str
    measures: tuple[DiscoveryMeasure, ...]
    created_at: str
    context_ids: tuple[str, ...] = ()
    related_finding_id: str | None = None
    expectation: DiscoveryExpectation | None = None
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_uuid(self.id, "id")
        if not isinstance(self.kind, DiscoveryFindingKind):
            raise ValueError("kind must be a DiscoveryFindingKind")
        _require_text(self.title, "title")
        _require_text(self.description, "description")
        if not self.input_ids:
            raise ValueError("discovery finding requires at least one input")
        for input_id in self.input_ids:
            _require_uuid(input_id, "input_id")
        for context_id in self.context_ids:
            _require_uuid(context_id, "context_id")
        _require_text(self.method, "method")
        _require_text(self.method_version, "method_version")
        _require_text(self.rationale, "rationale")
        _require_iso_timestamp(self.created_at, "created_at")
        for measure in self.measures:
            if not isinstance(measure, DiscoveryMeasure):
                raise ValueError("measures must contain DiscoveryMeasure objects")
        if self.related_finding_id is not None:
            _require_uuid(self.related_finding_id, "related_finding_id")
        if self.expectation is not None and not isinstance(self.expectation, DiscoveryExpectation):
            raise ValueError("expectation must be a DiscoveryExpectation")
        if self.kind is DiscoveryFindingKind.GAP and self.expectation is None:
            raise ValueError("gap finding requires explicit expectation")
        if self.kind not in {DiscoveryFindingKind.GAP, DiscoveryFindingKind.UNRESOLVED_QUESTION} and self.expectation is not None:
            raise ValueError("only gap and unresolved-question findings may carry an expectation")
        if self.kind is DiscoveryFindingKind.UNRESOLVED_QUESTION and self.related_finding_id is None:
            raise ValueError("unresolved question requires related_finding_id")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version: {self.schema_version}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind.value,
            "title": self.title,
            "description": self.description,
            "input_ids": list(self.input_ids),
            "context_ids": list(self.context_ids),
            "method": self.method,
            "method_version": self.method_version,
            "rationale": self.rationale,
            "measures": [measure.to_dict() for measure in self.measures],
            "created_at": self.created_at,
            "related_finding_id": self.related_finding_id,
            "expectation": self.expectation.to_dict() if self.expectation is not None else None,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DiscoveryFinding":
        expectation_data = data.get("expectation")
        if expectation_data is None:
            expectation = None
        elif isinstance(expectation_data, (list, tuple)):
            if len(expectation_data) != 3:
                raise ValueError("legacy expectation must contain subject_id, predicate, and object_id")
            expectation = DiscoveryExpectation(
                kind=DiscoveryExpectationKind.RELATIONSHIP,
                data={
                    "subject_id": expectation_data[0],
                    "predicate": expectation_data[1],
                    "object_id": expectation_data[2],
                },
            )
        else:
            expectation = DiscoveryExpectation.from_dict(expectation_data)

        return cls(
            id=data["id"],
            kind=DiscoveryFindingKind(data["kind"]),
            title=data["title"],
            description=data["description"],
            input_ids=tuple(data["input_ids"]),
            context_ids=tuple(data.get("context_ids", ())),
            method=data["method"],
            method_version=data["method_version"],
            rationale=data["rationale"],
            measures=tuple(DiscoveryMeasure.from_dict(item) for item in data["measures"]),
            created_at=data["created_at"],
            related_finding_id=data.get("related_finding_id"),
            expectation=expectation,
            schema_version=data.get("schema_version", SCHEMA_VERSION),
        )

@dataclass(frozen=True, slots=True)
class Hypothesis:
    """A generated candidate explanation, never grounded evidence."""
    id: str
    statement: str
    finding_ids: tuple[str, ...]
    input_ids: tuple[str, ...]
    method: str
    method_version: str
    rationale: str
    assumptions: tuple[str, ...]
    created_at: str
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_uuid(self.id, "id")
        _require_text(self.statement, "statement")
        if not self.finding_ids:
            raise ValueError("hypothesis requires at least one finding")
        for value in self.finding_ids:
            _require_uuid(value, "finding_id")
        for value in self.input_ids:
            _require_uuid(value, "input_id")
        _require_text(self.method, "method")
        _require_text(self.method_version, "method_version")
        _require_text(self.rationale, "rationale")
        for value in self.assumptions:
            _require_text(value, "assumption")
        _require_iso_timestamp(self.created_at, "created_at")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version: {self.schema_version}")

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "statement": self.statement,
                "finding_ids": list(self.finding_ids), "input_ids": list(self.input_ids),
                "method": self.method, "method_version": self.method_version,
                "rationale": self.rationale, "assumptions": list(self.assumptions),
                "created_at": self.created_at, "schema_version": self.schema_version}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Hypothesis":
        return cls(id=data["id"], statement=data["statement"],
                   finding_ids=tuple(data["finding_ids"]),
                   input_ids=tuple(data.get("input_ids", ())),
                   method=data["method"], method_version=data["method_version"],
                   rationale=data["rationale"], assumptions=tuple(data["assumptions"]),
                   created_at=data["created_at"],
                   schema_version=data.get("schema_version", SCHEMA_VERSION))


@dataclass(frozen=True, slots=True)
class Model:
    """A generated structured explanatory representation."""
    id: str
    description: str
    hypothesis_ids: tuple[str, ...]
    input_ids: tuple[str, ...]
    assumptions: tuple[str, ...]
    method: str
    method_version: str
    rationale: str
    created_at: str
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_uuid(self.id, "id")
        _require_text(self.description, "description")
        if not self.hypothesis_ids and not self.input_ids:
            raise ValueError("model requires a hypothesis or grounded/integrity input")
        for value in (*self.hypothesis_ids, *self.input_ids):
            _require_uuid(value, "model input_id")
        for value in self.assumptions:
            _require_text(value, "assumption")
        _require_text(self.method, "method")
        _require_text(self.method_version, "method_version")
        _require_text(self.rationale, "rationale")
        _require_iso_timestamp(self.created_at, "created_at")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version: {self.schema_version}")

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "description": self.description,
                "hypothesis_ids": list(self.hypothesis_ids), "input_ids": list(self.input_ids),
                "assumptions": list(self.assumptions), "method": self.method,
                "method_version": self.method_version, "rationale": self.rationale,
                "created_at": self.created_at, "schema_version": self.schema_version}

    @classmethod    def from_dict(cls, data: Mapping[str, Any]) -> "Model":
        return cls(id=data["id"], description=data["description"],
                   hypothesis_ids=tuple(data.get("hypothesis_ids", ())),
                   input_ids=tuple(data.get("input_ids", ())),
                   assumptions=tuple(data["assumptions"]), method=data["method"],
                   method_version=data["method_version"], rationale=data["rationale"],
                   created_at=data["created_at"],
                   schema_version=data.get("schema_version", SCHEMA_VERSION))


@dataclass(frozen=True, slots=True)
class Prediction:
    """A generated, bounded consequence of a hypothesis or model."""
    id: str
    source_id: str
    consequence: str
    conditions: str
    assumptions: tuple[str, ...]
    method: str
    method_version: str
    rationale: str
    comparison_hypothesis_ids: tuple[str, ...]
    created_at: str
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_uuid(self.id, "id")
        _require_uuid(self.source_id, "source_id")
        _require_text(self.consequence, "consequence")
        _require_text(self.conditions, "conditions")
        for value in self.assumptions:
            _require_text(value, "assumption")
        _require_text(self.method, "method")
        _require_text(self.method_version, "method_version")
        _require_text(self.rationale, "rationale")
        for value in self.comparison_hypothesis_ids:
            _require_uuid(value, "comparison_hypothesis_id")
        if self.comparison_hypothesis_ids:
            if len(self.comparison_hypothesis_ids) < 2:
                raise ValueError("distinguishing prediction requires at least two hypotheses")
            if self.source_id not in self.comparison_hypothesis_ids:
                raise ValueError("distinguishing prediction must include its source hypothesis")
        _require_iso_timestamp(self.created_at, "created_at")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version: {self.schema_version}")

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "source_id": self.source_id,
                "consequence": self.consequence, "conditions": self.conditions,
                "assumptions": list(self.assumptions), "method": self.method,
                "method_version": self.method_version, "rationale": self.rationale,
                "comparison_hypothesis_ids": list(self.comparison_hypothesis_ids),
                "created_at": self.created_at, "schema_version": self.schema_version}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Prediction":
        return cls(id=data["id"], source_id=data["source_id"],
                   consequence=data["consequence"], conditions=data["conditions"],
                   assumptions=tuple(data["assumptions"]), method=data["method"],
                   method_version=data["method_version"], rationale=data["rationale"],
                   comparison_hypothesis_ids=tuple(data.get("comparison_hypothesis_ids", ())),
                   created_at=data["created_at"],
                   schema_version=data.get("schema_version", SCHEMA_VERSION))



@dataclass(frozen=True, slots=True)
class ExperimentProposal:
    """A generated plan for obtaining observations to test predictions."""
    id: str
    prediction_ids: tuple[str, ...]
    objective: str
    proposed_observation: str
    discrimination_basis: str
    conditions: str
    assumptions: tuple[str, ...]
    method: str
    method_version: str
    rationale: str
    created_at: str
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_uuid(self.id, "id")
        if not self.prediction_ids:
            raise ValueError("experiment proposal requires at least one prediction")
        for value in self.prediction_ids:
            _require_uuid(value, "prediction_id")
        _require_text(self.objective, "objective")
        _require_text(self.proposed_observation, "proposed_observation")
        _require_text(self.discrimination_basis, "discrimination_basis")
        _require_text(self.conditions, "conditions")
        for value in self.assumptions:
            _require_text(value, "assumption")
        _require_text(self.method, "method")
        _require_text(self.method_version, "method_version")
        _require_text(self.rationale, "rationale")
        _require_iso_timestamp(self.created_at, "created_at")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version: {self.schema_version}")

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "prediction_ids": list(self.prediction_ids),
                "objective": self.objective, "proposed_observation": self.proposed_observation,
                "discrimination_basis": self.discrimination_basis,
                "conditions": self.conditions, "assumptions": list(self.assumptions),
                "method": self.method, "method_version": self.method_version,
                "rationale": self.rationale, "created_at": self.created_at,
                "schema_version": self.schema_version}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExperimentProposal":
        return cls(id=data["id"], prediction_ids=tuple(data["prediction_ids"]),
                   objective=data["objective"], proposed_observation=data["proposed_observation"],
                   discrimination_basis=data["discrimination_basis"], conditions=data["conditions"], assumptions=tuple(data["assumptions"]),
                   method=data["method"], method_version=data["method_version"],
                   rationale=data["rationale"], created_at=data["created_at"],
                   schema_version=data.get("schema_version", SCHEMA_VERSION))

@dataclass(frozen=True, slots=True)
class PredictionEvaluation:
    """A generated contextual evaluation of one result against one prediction."""

    id: str
    result_id: str
    prediction_id: str
    experiment_proposal_id: str | None
    comparison_conditions: str
    assumptions: tuple[str, ...]
    outcome: PredictionEvaluationOutcome
    rationale: str
    method: str
    method_version: str
    created_at: str
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_uuid(self.id, "id")
        _require_uuid(self.result_id, "result_id")
        _require_uuid(self.prediction_id, "prediction_id")
        if self.experiment_proposal_id is not None:
            _require_uuid(self.experiment_proposal_id, "experiment_proposal_id")
        _require_text(self.comparison_conditions, "comparison_conditions")
        for value in self.assumptions:
            _require_text(value, "assumption")
        if not isinstance(self.outcome, PredictionEvaluationOutcome):
            raise ValueError("outcome must be a PredictionEvaluationOutcome")
        _require_text(self.rationale, "rationale")
        _require_text(self.method, "method")
        _require_text(self.method_version, "method_version")
        _require_iso_timestamp(self.created_at, "created_at")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version: {self.schema_version}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "result_id": self.result_id,
            "prediction_id": self.prediction_id,
            "experiment_proposal_id": self.experiment_proposal_id,
            "comparison_conditions": self.comparison_conditions,
            "assumptions": list(self.assumptions),
            "outcome": self.outcome.value,
            "rationale": self.rationale,
            "method": self.method,
            "method_version": self.method_version,
            "created_at": self.created_at,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PredictionEvaluation":
        return cls(
            id=data["id"],
            result_id=data["result_id"],
            prediction_id=data["prediction_id"],
            experiment_proposal_id=data.get("experiment_proposal_id"),
            comparison_conditions=data["comparison_conditions"],
            assumptions=tuple(data["assumptions"]),
            outcome=PredictionEvaluationOutcome(data["outcome"]),
            rationale=data["rationale"],
            method=data["method"],
            method_version=data["method_version"],
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