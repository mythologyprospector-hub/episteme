"""Generated assessment of a candidate against one explicit constraint.

This module records assessment metadata only. It is never grounded evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping

from .model import SCHEMA_VERSION, _require_iso_timestamp, _require_text, _require_uuid


class CandidateConstraintStatus(StrEnum):
    """Current assessment state of a candidate against a constraint."""

    SATISFIED = "satisfied"
    VIOLATED = "violated"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class CandidateConstraintAssessment:
    """One inspectable, non-grounded assessment of a candidate constraint."""

    id: str
    candidate_id: str
    constraint_id: str
    basis: str
    status: CandidateConstraintStatus
    input_ids: tuple[str, ...]
    assumptions: tuple[str, ...]
    explanation: str
    method: str
    method_version: str
    created_at: str
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_uuid(self.id, "id")
        _require_uuid(self.candidate_id, "candidate_id")
        _require_text(self.constraint_id, "constraint_id")
        _require_text(self.basis, "basis")
        if not isinstance(self.status, CandidateConstraintStatus):
            raise ValueError("status must be a CandidateConstraintStatus")
        for input_id in self.input_ids:
            _require_uuid(input_id, "input_id")
        for assumption in self.assumptions:
            _require_text(assumption, "assumption")
        _require_text(self.explanation, "explanation")
        _require_text(self.method, "method")
        _require_text(self.method_version, "method_version")
        _require_iso_timestamp(self.created_at, "created_at")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version: {self.schema_version}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "candidate_id": self.candidate_id,
            "constraint_id": self.constraint_id,
            "basis": self.basis,
            "status": self.status.value,
            "input_ids": list(self.input_ids),
            "assumptions": list(self.assumptions),
            "explanation": self.explanation,
            "method": self.method,
            "method_version": self.method_version,
            "created_at": self.created_at,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CandidateConstraintAssessment":
        return cls(
            id=data["id"],
            candidate_id=data["candidate_id"],
            constraint_id=data["constraint_id"],
            basis=data["basis"],
            status=CandidateConstraintStatus(data["status"]),
            input_ids=tuple(data.get("input_ids", ())),
            assumptions=tuple(data.get("assumptions", ())),
            explanation=data["explanation"],
            method=data["method"],
            method_version=data["method_version"],
            created_at=data["created_at"],
            schema_version=data.get("schema_version", SCHEMA_VERSION),
        )
