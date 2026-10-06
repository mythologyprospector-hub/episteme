"""Durable model for assessing generated exploration observations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .model import SCHEMA_VERSION, Provenance, _require_iso_timestamp, _require_text, _require_uuid


@dataclass(frozen=True, slots=True)
class ExplorationObservationAssessment:
    """A durable assessment of a generated exploration observation."""

    id: str
    observation_id: str
    accepted: bool
    method: str
    method_version: str
    rationale: str
    provenance: tuple[Provenance, ...]
    assessed_at: str
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_uuid(self.id, "id")
        _require_uuid(self.observation_id, "observation_id")
        if not isinstance(self.accepted, bool):
            raise ValueError("accepted must be a bool")
        _require_text(self.method, "method")
        _require_text(self.method_version, "method_version")
        _require_text(self.rationale, "rationale")
        if not self.provenance:
            raise ValueError("exploration observation assessment requires provenance")
        _require_iso_timestamp(self.assessed_at, "assessed_at")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version: {self.schema_version}")
        for entry in self.provenance:
            if not isinstance(entry, Provenance):
                raise ValueError("provenance entries must be Provenance objects")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "observation_id": self.observation_id,
            "accepted": self.accepted,
            "method": self.method,
            "method_version": self.method_version,
            "rationale": self.rationale,
            "provenance": [item.to_dict() for item in self.provenance],
            "assessed_at": self.assessed_at,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExplorationObservationAssessment":
        return cls(
            id=data["id"],
            observation_id=data["observation_id"],
            accepted=data["accepted"],
            method=data["method"],
            method_version=data["method_version"],
            rationale=data["rationale"],
            provenance=tuple(Provenance.from_dict(item) for item in data["provenance"]),
            assessed_at=data["assessed_at"],
            schema_version=data.get("schema_version", SCHEMA_VERSION),
        )
