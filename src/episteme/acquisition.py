"""Provider-neutral bounded external acquisition."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping
from uuid import uuid4

from .capture import CaptureOutcome, CapturedRepresentation
from .model import canonical_json
from .store import Store


@dataclass(frozen=True, slots=True)
class AcquisitionRequest:
    """A finite request for one external resource."""

    source_id: str
    requested_resource: str
    request_parameters: Mapping[str, Any]
    acquisition_method: str
    acquisition_method_version: str

    def __post_init__(self) -> None:
        if not self.source_id.strip() or not self.requested_resource.strip():
            raise ValueError("acquisition source_id and requested_resource must be non-empty")
        if not self.acquisition_method.strip() or not self.acquisition_method_version.strip():
            raise ValueError("acquisition method and version must be non-empty")
        canonical_json(self.request_parameters)


@dataclass(frozen=True, slots=True)
class AcquisitionResponse:
    """Observed provider response before it is persisted as a capture."""

    status: int | None
    media_type: str | None
    source_version: str | None
    content: bytes | None
    outcome: CaptureOutcome
    error: str | None = None

    def __post_init__(self) -> None:
        if self.status is not None and not 100 <= self.status <= 599:
            raise ValueError("acquisition response status must be an HTTP status code")
        if self.outcome is CaptureOutcome.FAILED:
            if self.content is not None:
                raise ValueError("failed acquisition response cannot carry content")
            if not self.error:
                raise ValueError("failed acquisition response requires an error")
        elif self.content is None:
            raise ValueError("successful or partial acquisition response requires content")
        elif self.error is not None:
            raise ValueError("successful or partial acquisition response cannot carry an error")


AcquisitionProvider = Callable[[AcquisitionRequest], AcquisitionResponse]


def acquire(
    request: AcquisitionRequest,
    provider: AcquisitionProvider,
    store: Store,
    *,
    captured_at: str,
    capture_id: str | None = None,
) -> CapturedRepresentation:
    """Perform one bounded acquisition and persist its Phase 19 capture."""

    try:
        response = provider(request)
    except Exception as exc:
        response = AcquisitionResponse(
            status=None,
            media_type=None,
            source_version=None,
            content=None,
            outcome=CaptureOutcome.FAILED,
            error=f"{type(exc).__name__}: {exc}",
        )

    content_digest = None
    content_reference = None
    if response.content is not None:
        import hashlib

        content_digest = hashlib.sha256(response.content).hexdigest()
        content_reference = f"sha256/{content_digest}"

    capture = CapturedRepresentation(
        id=capture_id or str(uuid4()),
        source_id=request.source_id,
        requested_resource=request.requested_resource,
        request_parameters=request.request_parameters,
        captured_at=captured_at,
        response_status=response.status,
        media_type=response.media_type,
        source_version=response.source_version,
        content_digest=content_digest,
        content_reference=content_reference,
        acquisition_method=request.acquisition_method,
        acquisition_method_version=request.acquisition_method_version,
        outcome=response.outcome,
        error=response.error,
    )
    store.put_captured_representation(capture, response.content)
    return capture
