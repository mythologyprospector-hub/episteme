"""Durable representations of material captured from external sources."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class CaptureOutcome(str, Enum):
    """Outcome of an external acquisition attempt."""

    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass(frozen=True)
class CapturedRepresentation:
    """Immutable metadata describing one externally captured representation."""

    id: str
    source_id: str
    requested_resource: str
    request_parameters: Mapping[str, Any]
    captured_at: str
    response_status: int | None
    media_type: str | None
    source_version: str | None
    content_digest: str | None
    content_reference: str | None
    acquisition_method: str
    acquisition_method_version: str
    outcome: CaptureOutcome
    schema_version: int = 1

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("capture id must be non-empty")
        if not self.source_id:
            raise ValueError("capture source_id must be non-empty")
        if not self.requested_resource:
            raise ValueError("capture requested_resource must be non-empty")
        if not self.captured_at:
            raise ValueError("capture captured_at must be non-empty")
        if not self.acquisition_method:
            raise ValueError("capture acquisition_method must be non-empty")
        if not self.acquisition_method_version:
            raise ValueError("capture acquisition_method_version must be non-empty")
        if self.response_status is not None and not 100 <= self.response_status <= 599:
            raise ValueError("capture response_status must be an HTTP status code")
        if self.outcome is CaptureOutcome.FAILED:
            if self.content_digest is not None or self.content_reference is not None:
                raise ValueError("failed capture cannot reference captured content")
        elif (self.content_digest is None) != (self.content_reference is None):
            raise ValueError("content_digest and content_reference must be supplied together")
        if self.content_digest is not None:
            if len(self.content_digest) != 64 or any(
                character not in "0123456789abcdef" for character in self.content_digest
            ):
                raise ValueError("capture content_digest must be a lowercase SHA-256 digest")
        if self.content_reference is not None:
            if not self.content_reference.startswith("sha256/"):
                raise ValueError("capture content_reference must use the sha256/<digest> form")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "requested_resource": self.requested_resource,
            "request_parameters": dict(self.request_parameters),
            "captured_at": self.captured_at,
            "response_status": self.response_status,
            "media_type": self.media_type,
            "source_version": self.source_version,
            "content_digest": self.content_digest,
            "content_reference": self.content_reference,
            "acquisition_method": self.acquisition_method,
            "acquisition_method_version": self.acquisition_method_version,
            "outcome": self.outcome.value,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CapturedRepresentation":
        return cls(
            id=str(data["id"]),
            source_id=str(data["source_id"]),
            requested_resource=str(data["requested_resource"]),
            request_parameters=dict(data.get("request_parameters", {})),
            captured_at=str(data["captured_at"]),
            response_status=data.get("response_status"),
            media_type=data.get("media_type"),
            source_version=data.get("source_version"),
            content_digest=data.get("content_digest"),
            content_reference=data.get("content_reference"),
            acquisition_method=str(data["acquisition_method"]),
            acquisition_method_version=str(data["acquisition_method_version"]),
            outcome=CaptureOutcome(data["outcome"]),
            schema_version=int(data.get("schema_version", 1)),
        )
