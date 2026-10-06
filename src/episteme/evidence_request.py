"""Host-owned bounded evidence-request execution for Phase 28.

The planner names a registered capability and supplies only bounded parameters.
The capability owns the concrete acquisition resource and method.  Execution
then delegates to the existing acquisition pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID

from .acquisition import AcquisitionProvider, AcquisitionRequest, acquire
from .store import Store


@dataclass(frozen=True, slots=True)
class EvidenceCapability:
    """A host-registered acquisition capability."""

    name: str
    source_id: str
    requested_resource: str
    acquisition_method: str
    acquisition_method_version: str
    allowed_parameters: frozenset[str]
    supported_media_types: frozenset[str]

    def validate_representation(self, representation: str) -> None:
        if representation not in self.supported_media_types:
            raise ValueError(
                "unsupported evidence request representation: " + representation
            )

    def validate_response_media_type(self, media_type: str | None) -> None:
        if media_type not in self.supported_media_types:
            raise ValueError(
                "acquisition response media type is not supported by evidence capability: "
                + str(media_type)
            )

    def build_request(self, parameters: Mapping[str, Any]) -> AcquisitionRequest:
        if not isinstance(parameters, Mapping):
            raise ValueError("evidence capability parameters must be a mapping")

        unknown = set(parameters) - self.allowed_parameters
        if unknown:
            raise ValueError(
                "unsupported evidence capability parameters: "
                + ", ".join(sorted(map(str, unknown)))
            )

        if self.name == "crossref_works":
            if "rows" in parameters:
                rows = parameters["rows"]
                if isinstance(rows, bool) or not isinstance(rows, int) or not 1 <= rows <= 1000:
                    raise ValueError("evidence capability rows must be an integer from 1 to 1000")
            if "query.title" in parameters:
                title = parameters["query.title"]
                if not isinstance(title, str) or not title.strip():
                    raise ValueError("evidence capability query.title must be non-empty")

        return AcquisitionRequest(
            source_id=self.source_id,
            requested_resource=self.requested_resource,
            request_parameters=dict(parameters),
            acquisition_method=self.acquisition_method,
            acquisition_method_version=self.acquisition_method_version,
        )


@dataclass(frozen=True, slots=True)
class EvidenceRequest:
    """Planner-facing request for one host-owned evidence capability."""

    capability: str
    parameters: Mapping[str, Any]
    rationale: str
    motivation_ids: tuple[str, ...] = ()
    requested_representation: str = ""

    def __post_init__(self) -> None:
        if not self.capability.strip():
            raise ValueError("evidence request capability must be non-empty")
        if not self.rationale.strip():
            raise ValueError("evidence request rationale must be non-empty")
        if not self.requested_representation.strip():
            raise ValueError("evidence request representation must be non-empty")
        if not isinstance(self.parameters, Mapping):
            raise ValueError("evidence request parameters must be a mapping")
        object.__setattr__(self, "parameters", MappingProxyType(dict(self.parameters)))
        if not self.motivation_ids:
            raise ValueError("evidence request requires at least one motivation")
        object.__setattr__(self, "motivation_ids", tuple(self.motivation_ids))
        for motivation_id in self.motivation_ids:
            if not isinstance(motivation_id, str) or not motivation_id.strip():
                raise ValueError("evidence request motivation ids must be non-empty strings")
            try:
                UUID(motivation_id)
            except ValueError as exc:
                raise ValueError("evidence request motivation ids must be UUID strings") from exc


_CROSSREF_WORKS = EvidenceCapability(
    name="crossref_works",
    source_id="crossref",
    requested_resource="https://api.crossref.org/v1/works",
    acquisition_method="crossref-rest",
    acquisition_method_version="1",
    allowed_parameters=frozenset({"rows", "query.title"}),
    supported_media_types=frozenset({"application/json"}),
)


def resolve_evidence_capability(name: str) -> EvidenceCapability:
    """Resolve only explicitly registered host capabilities."""
    if name == _CROSSREF_WORKS.name:
        return _CROSSREF_WORKS
    raise ValueError(f"unknown evidence capability: {name}")


def execute_evidence_request(
    request: EvidenceRequest,
    store: Store,
    *,
    provider: AcquisitionProvider,
    captured_at: str,
    capture_id: str | None = None,
):
    """Execute an admitted request through the existing acquisition pipeline."""
    capability = resolve_evidence_capability(request.capability)

    capability.validate_representation(request.requested_representation)
    acquisition_request = capability.build_request(request.parameters)

    missing_motivations = [
        motivation_id
        for motivation_id in request.motivation_ids
        if not store.epistemic_object_exists(motivation_id)
    ]
    if missing_motivations:
        raise ValueError(
            "evidence request motivation not found: "
            + ", ".join(missing_motivations)
        )

    def bounded_provider(acquisition: AcquisitionRequest):
        response = provider(acquisition)
        if response.outcome.value != "failed":
            capability.validate_response_media_type(response.media_type)
        return response

    return acquire(
        acquisition_request,
        bounded_provider,
        store,
        captured_at=captured_at,
        capture_id=capture_id,
    )
