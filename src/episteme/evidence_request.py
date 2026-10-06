"""Host-owned bounded evidence-request execution for Phase 28.

The planner names a registered capability and supplies only bounded parameters.
The capability owns the concrete acquisition resource and method.  Execution
then delegates to the existing acquisition pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
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

    def build_request(self, parameters: Mapping[str, Any]) -> AcquisitionRequest:
        if not isinstance(parameters, Mapping):
            raise ValueError("evidence capability parameters must be a mapping")

        unknown = set(parameters) - self.allowed_parameters
        if unknown:
            raise ValueError(
                "unsupported evidence capability parameters: "
                + ", ".join(sorted(map(str, unknown)))
            )

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

    def __post_init__(self) -> None:
        if not self.capability.strip():
            raise ValueError("evidence request capability must be non-empty")
        if not self.rationale.strip():
            raise ValueError("evidence request rationale must be non-empty")
        if not self.motivation_ids:
            raise ValueError("evidence request requires at least one motivation")
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
    acquisition_request = capability.build_request(request.parameters)
    return acquire(
        acquisition_request,
        provider,
        store,
        captured_at=captured_at,
        capture_id=capture_id,
    )
