"""Phase 28 contract tests for bounded autonomous evidence requests.

These tests intentionally describe the host-owned boundary before runtime
implementation.  They are expected to fail until the Phase 28 contract exists.
"""

import pytest

from episteme import AcquisitionRequest, AcquisitionResponse, CaptureOutcome, Store


CAPTURED_AT = "2026-10-06T12:00:00Z"
CONTENT = b'{"message":{"items":[{"DOI":"10.1234/example"}]}}'


def _request(**overrides):
    from episteme import acquire

    values = {
        "source_id": "crossref",
        "requested_resource": "https://api.crossref.org/v1/works",
        "request_parameters": {"rows": 1, "query.title": "example"},
        "acquisition_method": "crossref-rest",
        "acquisition_method_version": "1",
    }
    values.update(overrides)
    return AcquisitionRequest(**values)


def test_existing_acquisition_request_remains_the_host_execution_object():
    request = _request()
    assert request.source_id == "crossref"
    assert request.requested_resource.endswith("/works")


def test_host_capability_resolution_rejects_unknown_capability_before_provider():
    from episteme.evidence_request import resolve_evidence_capability
    with pytest.raises(ValueError, match="unknown evidence capability"):
        resolve_evidence_capability("arbitrary-network-client")


def test_host_capability_resolution_returns_bounded_acquisition_factory():
    from episteme.evidence_request import resolve_evidence_capability
    capability = resolve_evidence_capability("crossref_works")
    request = capability.build_request({"rows": 1, "query.title": "example"})
    assert isinstance(request, AcquisitionRequest)
    assert request.source_id == "crossref"
    assert request.acquisition_method == "crossref-rest"


def test_evidence_request_cannot_supply_arbitrary_resource_or_method():
    from episteme.evidence_request import resolve_evidence_capability
    capability = resolve_evidence_capability("crossref_works")
    with pytest.raises(ValueError):
        capability.build_request({
            "requested_resource": "https://evil.example/",
            "acquisition_method": "shell",
            "rows": 1,
        })


def test_admitted_evidence_request_reuses_existing_acquire_and_persists_capture(tmp_path):
    from episteme.evidence_request import EvidenceRequest, execute_evidence_request
    calls = []

    def provider(request):
        calls.append(request)
        return AcquisitionResponse(
            status=200, media_type="application/json",
            source_version="etag-phase28", content=CONTENT,
            outcome=CaptureOutcome.COMPLETE,
        )

    request = EvidenceRequest(
        capability="crossref_works",
        parameters={"rows": 1, "query.title": "example"},
        rationale="Discriminate the current candidate hypotheses.",
        motivation_ids=("11111111-1111-4111-8111-111111111111",),
    )

    with Store(tmp_path / "phase28.sqlite", capture_root=tmp_path / "captures") as store:
        result = execute_evidence_request(
            request, store, provider=provider,
            captured_at=CAPTURED_AT, capture_id="capture-phase28-success",
        )
        assert result.outcome is CaptureOutcome.COMPLETE
        assert result.id == "capture-phase28-success"
        assert calls
        assert store.read_captured_content(result.id) == CONTENT


def test_provider_failure_remains_failed_capture(tmp_path):
    from episteme.evidence_request import EvidenceRequest, execute_evidence_request
    request = EvidenceRequest(
        capability="crossref_works",
        parameters={"rows": 1},
        rationale="Test bounded failure handling.",
        motivation_ids=("22222222-2222-4222-8222-222222222222",),
    )

    def provider(_request):
        raise TimeoutError("provider timeout")

    with Store(tmp_path / "phase28.sqlite") as store:
        result = execute_evidence_request(
            request, store, provider=provider,
            captured_at=CAPTURED_AT, capture_id="capture-phase28-failure",
        )
        assert result.outcome is CaptureOutcome.FAILED
        assert result.error == "TimeoutError: provider timeout"


def test_partial_capture_remains_partial(tmp_path):
    from episteme.evidence_request import EvidenceRequest, execute_evidence_request
    request = EvidenceRequest(
        capability="crossref_works",
        parameters={"rows": 1},
        rationale="Test bounded partial acquisition handling.",
        motivation_ids=("33333333-3333-4333-8333-333333333333",),
    )

    def provider(_request):
        return AcquisitionResponse(
            status=206, media_type="application/json",
            source_version="etag-partial", content=CONTENT,
            outcome=CaptureOutcome.PARTIAL,
        )

    with Store(tmp_path / "phase28.sqlite", capture_root=tmp_path / "captures") as store:
        result = execute_evidence_request(
            request, store, provider=provider,
            captured_at=CAPTURED_AT, capture_id="capture-phase28-partial",
        )
        assert result.outcome is CaptureOutcome.PARTIAL
        assert store.read_captured_content(result.id) == CONTENT


def test_evidence_request_requires_a_discriminating_rationale():
    from episteme.evidence_request import EvidenceRequest
    with pytest.raises(ValueError, match="rationale"):
        EvidenceRequest(
            capability="crossref_works",
            parameters={"rows": 1},
            rationale="",
            motivation_ids=("44444444-4444-4444-8444-444444444444",),
        )


def test_evidence_request_rejects_missing_motivation_before_provider(tmp_path):
    from episteme.evidence_request import EvidenceRequest, execute_evidence_request

    request = EvidenceRequest(
        capability="crossref_works",
        parameters={"rows": 1},
        rationale="Discriminate the current candidate hypotheses.",
        motivation_ids=("99999999-9999-4999-8999-999999999999",),
    )

    def provider(_request):
        raise AssertionError("provider must not run for an unknown motivation")

    with Store(tmp_path / "phase28.sqlite") as store:
        with pytest.raises(ValueError, match="motivation.*not found"):
            execute_evidence_request(
                request, store, provider=provider,
                captured_at=CAPTURED_AT, capture_id="capture-phase28-invalid-motivation",
            )


def test_evidence_request_requires_a_motivating_episteme_object():
    from episteme.evidence_request import EvidenceRequest

    with pytest.raises(ValueError, match="motivation"):
        EvidenceRequest(
            capability="crossref_works",
            parameters={"rows": 1},
            rationale="Discriminate the current candidate hypotheses.",
            motivation_ids=(),
        )

    request = EvidenceRequest(
        capability="crossref_works",
        parameters={"rows": 1},
        rationale="Discriminate the current candidate hypotheses.",
        motivation_ids=("11111111-1111-4111-8111-111111111111",),
    )
    assert request.motivation_ids == ("11111111-1111-4111-8111-111111111111",)
