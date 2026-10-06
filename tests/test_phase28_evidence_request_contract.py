"""Phase 28 contract tests for bounded autonomous evidence requests.

These tests lock the host-owned Phase 28 boundary as executable behavior.
"""

import pytest

from episteme import AcquisitionRequest, AcquisitionResponse, CaptureOutcome, Store
from episteme.model import Provenance, Record, RecordKind


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


def _seed_motivation(store, motivation_id):
    store.put_record(
        Record(
            id=motivation_id,
            kind=RecordKind.OBSERVATION,
            payload={"phase": 28},
            provenance=(Provenance(source_id="phase28-test", captured_at=CAPTURED_AT),),
            created_at=CAPTURED_AT,
        )
    )


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
        requested_representation="application/json",
        motivation_ids=("11111111-1111-4111-8111-111111111111",),
    )

    with Store(tmp_path / "phase28.sqlite", capture_root=tmp_path / "captures") as store:
        _seed_motivation(store, "11111111-1111-4111-8111-111111111111")
        result = execute_evidence_request(
            request, store, provider=provider,
            captured_at=CAPTURED_AT, capture_id="capture-phase28-success",
        )
        assert result.outcome is CaptureOutcome.COMPLETE
        assert result.id == "capture-phase28-success"
        assert calls
        assert store.read_captured_content(result.id) == CONTENT


def test_admitted_request_capture_preserves_host_owned_acquisition_metadata(tmp_path):
    from episteme.evidence_request import EvidenceRequest, execute_evidence_request

    motivation_id = "12121212-1212-4121-8121-121212121212"
    request = EvidenceRequest(
        capability="crossref_works",
        parameters={"rows": 7, "query.title": "bounded discovery"},
        rationale="Discriminate the current candidate hypotheses.",
        requested_representation="application/json",
        motivation_ids=(motivation_id,),
    )

    with Store(tmp_path / "phase28.sqlite", capture_root=tmp_path / "captures") as store:
        _seed_motivation(store, motivation_id)
        result = execute_evidence_request(
            request,
            store,
            provider=lambda _request: AcquisitionResponse(
                status=200,
                media_type="application/json",
                source_version="etag-phase28",
                content=CONTENT,
                outcome=CaptureOutcome.COMPLETE,
            ),
            captured_at=CAPTURED_AT,
            capture_id="capture-phase28-host-metadata",
        )

        assert result.source_id == "crossref"
        assert result.requested_resource == "https://api.crossref.org/v1/works"
        assert result.request_parameters == request.parameters
        assert result.acquisition_method == "crossref-rest"
        assert result.acquisition_method_version == "1"


def test_provider_failure_remains_failed_capture(tmp_path):
    from episteme.evidence_request import EvidenceRequest, execute_evidence_request
    request = EvidenceRequest(
        capability="crossref_works",
        parameters={"rows": 1},
        rationale="Test bounded failure handling.",
        requested_representation="application/json",
        motivation_ids=("22222222-2222-4222-8222-222222222222",),
    )

    def provider(_request):
        raise TimeoutError("provider timeout")

    with Store(tmp_path / "phase28.sqlite") as store:
        _seed_motivation(store, "22222222-2222-4222-8222-222222222222")
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
        requested_representation="application/json",
        motivation_ids=("33333333-3333-4333-8333-333333333333",),
    )

    def provider(_request):
        return AcquisitionResponse(
            status=206, media_type="application/json",
            source_version="etag-partial", content=CONTENT,
            outcome=CaptureOutcome.PARTIAL,
        )

    with Store(tmp_path / "phase28.sqlite", capture_root=tmp_path / "captures") as store:
        _seed_motivation(store, "33333333-3333-4333-8333-333333333333")
        result = execute_evidence_request(
            request, store, provider=provider,
            captured_at=CAPTURED_AT, capture_id="capture-phase28-partial",
        )
        assert result.outcome is CaptureOutcome.PARTIAL
        assert store.read_captured_content(result.id) == CONTENT




def test_evidence_request_rejects_non_epistemic_workflow_artifact_as_motivation(tmp_path):
    from episteme.acquisition import AcquisitionResponse, acquire
    from episteme.capture import CaptureOutcome
    from episteme.evidence_request import EvidenceRequest, execute_evidence_request

    capture_motivation_id = "88888888-8888-4888-8888-888888888888"

    with Store(tmp_path / "phase28.sqlite", capture_root=tmp_path / "captures") as store:
        acquire(
            _request(),
            lambda _request: AcquisitionResponse(
                status=200,
                media_type="application/json",
                source_version="v1",
                content=CONTENT,
                outcome=CaptureOutcome.COMPLETE,
            ),
            store,
            captured_at=CAPTURED_AT,
            capture_id=capture_motivation_id,
        )

        request = EvidenceRequest(
            capability="crossref_works",
            parameters={"rows": 1},
            rationale="Discriminate the current candidate hypotheses.",
            requested_representation="application/json",
            motivation_ids=(capture_motivation_id,),
        )

        def provider(_request):
            raise AssertionError("provider must not run for a non-epistemic motivation")

        with pytest.raises(ValueError, match="motivation.*not found"):
            execute_evidence_request(
                request,
                store,
                provider=provider,
                captured_at=CAPTURED_AT,
                capture_id="capture-phase28-invalid-capture-motivation",
            )

def test_crossref_capability_bounds_parameter_values():
    from episteme.evidence_request import resolve_evidence_capability

    capability = resolve_evidence_capability("crossref_works")

    with pytest.raises(ValueError, match="rows"):
        capability.build_request({"rows": 0})

    with pytest.raises(ValueError, match="rows"):
        capability.build_request({"rows": 1001})

    with pytest.raises(ValueError, match="query.title"):
        capability.build_request({"query.title": ""})

    request = capability.build_request({"rows": 10, "query.title": "example"})
    assert request.request_parameters == {"rows": 10, "query.title": "example"}


def test_invalid_bounded_parameters_do_not_create_capture(tmp_path):
    from episteme.evidence_request import EvidenceRequest, execute_evidence_request

    motivation_id = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
    request = EvidenceRequest(
        capability="crossref_works",
        parameters={"rows": 1001},
        rationale="Discriminate the current candidate hypotheses.",
        requested_representation="application/json",
        motivation_ids=(motivation_id,),
    )

    def provider(_request):
        raise AssertionError("provider must not run for rejected parameters")

    with Store(tmp_path / "phase28.sqlite", capture_root=tmp_path / "captures") as store:
        _seed_motivation(store, motivation_id)
        with pytest.raises(ValueError, match="rows"):
            execute_evidence_request(
                request,
                store,
                provider=provider,
                captured_at=CAPTURED_AT,
                capture_id="should-not-exist",
            )

        assert store.get_captured_representation("should-not-exist") is None


def test_invalid_bounded_parameters_are_rejected_before_provider(tmp_path):
    from episteme.evidence_request import EvidenceRequest, execute_evidence_request

    motivation_id = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
    request = EvidenceRequest(
        capability="crossref_works",
        parameters={"rows": 1001},
        rationale="Discriminate the current candidate hypotheses.",
        requested_representation="application/json",
        motivation_ids=(motivation_id,),
    )

    calls = []

    def provider(_request):
        calls.append(True)
        raise AssertionError("provider must not run for rejected parameters")

    with Store(tmp_path / "phase28.sqlite") as store:
        _seed_motivation(store, motivation_id)
        with pytest.raises(ValueError, match="rows"):
            execute_evidence_request(
                request,
                store,
                provider=provider,
                captured_at=CAPTURED_AT,
            )

    assert calls == []


def test_evidence_request_copies_motivation_ids_at_construction():
    from episteme.evidence_request import EvidenceRequest

    motivation_ids = ["99999999-9999-4999-8999-999999999999"]
    request = EvidenceRequest(
        capability="crossref_works",
        parameters={"rows": 3},
        rationale="Discriminate the current candidate hypotheses.",
        requested_representation="application/json",
        motivation_ids=motivation_ids,
    )

    motivation_ids.append("88888888-8888-4888-8888-888888888888")

    assert request.motivation_ids == (
        "99999999-9999-4999-8999-999999999999",
    )


def test_evidence_request_copies_parameter_mapping_at_construction():
    from episteme.evidence_request import EvidenceRequest

    parameters = {"rows": 3}
    request = EvidenceRequest(
        capability="crossref_works",
        parameters=parameters,
        rationale="Discriminate the current candidate hypotheses.",
        requested_representation="application/json",
        motivation_ids=("99999999-9999-4999-8999-999999999999",),
    )

    parameters["rows"] = 999

    assert request.parameters["rows"] == 3


def test_evidence_request_requires_requested_representation():
    from episteme.evidence_request import EvidenceRequest

    with pytest.raises(ValueError, match="representation"):
        EvidenceRequest(
            capability="crossref_works",
            parameters={"rows": 1},
            rationale="Discriminate the current candidate hypotheses.",
            motivation_ids=("11111111-1111-4111-8111-111111111111",),
            requested_representation="",
        )

    request = EvidenceRequest(
        capability="crossref_works",
        parameters={"rows": 1},
        rationale="Discriminate the current candidate hypotheses.",
        motivation_ids=("11111111-1111-4111-8111-111111111111",),
        requested_representation="application/json",
    )
    assert request.requested_representation == "application/json"

def test_evidence_request_rejects_mismatched_provider_media_type(tmp_path):
    from episteme.acquisition import AcquisitionResponse
    from episteme.capture import CaptureOutcome
    from episteme.evidence_request import EvidenceRequest, execute_evidence_request

    store = Store(tmp_path / "episteme.db")
    motivation_id = "99999999-9999-4999-8999-999999999999"
    _seed_motivation(store, motivation_id)

    request = EvidenceRequest(
        capability="crossref_works",
        parameters={"rows": 1},
        rationale="Discriminate the current candidate hypotheses.",
        requested_representation="application/json",
        motivation_ids=(motivation_id,),
    )

    def provider(_request):
        return AcquisitionResponse(
            status=200,
            media_type="text/html",
            source_version=None,
            content=b"<html>not json</html>",
            outcome=CaptureOutcome.COMPLETE,
        )

    capture = execute_evidence_request(
        request,
        store,
        provider=provider,
        captured_at="2026-10-06T00:00:00+00:00",
    )

    assert capture.outcome is CaptureOutcome.FAILED
    assert "media type" in (capture.error or "")
    assert capture.content_digest is None

def test_unsupported_evidence_representation_is_rejected_before_provider(tmp_path):
    from episteme.evidence_request import EvidenceRequest, execute_evidence_request

    motivation_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    request = EvidenceRequest(
        capability="crossref_works",
        parameters={"rows": 1},
        rationale="Discriminate the current candidate hypotheses.",
        requested_representation="text/html",
        motivation_ids=(motivation_id,),
    )

    calls = []

    def provider(_request):
        calls.append(True)
        raise AssertionError("provider must not run for rejected representation")

    with Store(tmp_path / "phase28.sqlite") as store:
        _seed_motivation(store, motivation_id)
        with pytest.raises(ValueError, match="unsupported evidence request representation"):
            execute_evidence_request(
                request,
                store,
                provider=provider,
                captured_at=CAPTURED_AT,
            )

    assert calls == []


def test_evidence_request_representation_must_be_supported_by_capability():
    from episteme.evidence_request import EvidenceRequest, resolve_evidence_capability

    capability = resolve_evidence_capability("crossref_works")
    request = EvidenceRequest(
        capability=capability.name,
        parameters={"rows": 1},
        rationale="Discriminate the current candidate hypotheses.",
        requested_representation="text/html",
        motivation_ids=("11111111-1111-4111-8111-111111111111",),
    )

    with pytest.raises(ValueError, match="representation"):
        capability.validate_representation(request.requested_representation)


def test_unresolved_question_is_a_valid_evidence_request_motivation(tmp_path):
    from episteme.discovery import question_from_finding
    from episteme.evidence_request import EvidenceRequest, execute_evidence_request
    from episteme.model import DiscoveryFinding, DiscoveryFindingKind

    finding_id = "55555555-5555-4555-8555-555555555555"
    request_id = "66666666-6666-4666-8666-666666666666"

    def provider(_request):
        return AcquisitionResponse(
            status=200,
            media_type="application/json",
            source_version="v1",
            content=CONTENT,
            outcome=CaptureOutcome.COMPLETE,
        )

    with Store(tmp_path / "phase28.sqlite", capture_root=tmp_path / "captures") as store:
        _seed_motivation(store, request_id)
        tension = DiscoveryFinding(
            id=finding_id,
            kind=DiscoveryFindingKind.TENSION,
            title="Phase 28 test tension",
            description="Two represented observations remain in tension.",
            input_ids=(request_id,),
            method="phase28-test",
            method_version="1",
            rationale="Create a bounded unresolved question for the evidence-request contract.",
            measures=(),
            created_at=CAPTURED_AT,
        )
        store.put_discovery_finding(tension)

        question = question_from_finding(tension, CAPTURED_AT)
        store.put_discovery_finding(question)

        request = EvidenceRequest(
            capability="crossref_works",
            parameters={"rows": 1},
            rationale="Acquire evidence to address the unresolved question.",
            requested_representation="application/json",
            motivation_ids=(question.id,),
        )
        result = execute_evidence_request(
            request,
            store,
            provider=provider,
            captured_at=CAPTURED_AT,
            capture_id="capture-phase28-question-motivation",
        )

        assert result.outcome is CaptureOutcome.COMPLETE
        assert result.id == "capture-phase28-question-motivation"


def test_evidence_request_requires_a_discriminating_rationale():
    from episteme.evidence_request import EvidenceRequest
    with pytest.raises(ValueError, match="rationale"):
        EvidenceRequest(
            capability="crossref_works",
            parameters={"rows": 1},
            rationale="",
            requested_representation="application/json",
            motivation_ids=("44444444-4444-4444-8444-444444444444",),
        )


def test_evidence_request_rejects_missing_motivation_before_provider(tmp_path):
    from episteme.evidence_request import EvidenceRequest, execute_evidence_request

    request = EvidenceRequest(
        capability="crossref_works",
        parameters={"rows": 1},
        rationale="Discriminate the current candidate hypotheses.",
        requested_representation="application/json",
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
            requested_representation="application/json",
            motivation_ids=(),
        )

    request = EvidenceRequest(
        capability="crossref_works",
        parameters={"rows": 1},
        rationale="Discriminate the current candidate hypotheses.",
        requested_representation="application/json",
        motivation_ids=("11111111-1111-4111-8111-111111111111",),
    )
    assert request.motivation_ids == ("11111111-1111-4111-8111-111111111111",)



def test_unknown_capability_is_rejected_before_provider_and_capture(tmp_path):
    from episteme.evidence_request import EvidenceRequest, execute_evidence_request

    motivation_id = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
    request = EvidenceRequest(
        capability="arbitrary-network-client",
        parameters={},
        rationale="Discriminate the current candidate hypotheses.",
        requested_representation="application/json",
        motivation_ids=(motivation_id,),
    )

    def provider(_request):
        raise AssertionError("provider must not run for an unknown capability")

    with Store(tmp_path / "phase28.sqlite", capture_root=tmp_path / "captures") as store:
        _seed_motivation(store, motivation_id)
        with pytest.raises(ValueError, match="unknown evidence capability"):
            execute_evidence_request(
                request,
                store,
                provider=provider,
                captured_at=CAPTURED_AT,
                capture_id="should-not-exist",
            )

        assert store.get_captured_representation("should-not-exist") is None


def test_unknown_capability_is_rejected_before_motivation_lookup(tmp_path):
    from episteme.evidence_request import EvidenceRequest, execute_evidence_request

    request = EvidenceRequest(
        capability="arbitrary-network-client",
        parameters={},
        rationale="Discriminate the current candidate hypotheses.",
        requested_representation="application/json",
        motivation_ids=("dddddddd-dddd-4ddd-8ddd-dddddddddddd",),
    )

    class ExplodingStore:
        def epistemic_object_exists(self, _object_id):
            raise AssertionError(
                "motivation lookup must not occur before capability admission"
            )

    with pytest.raises(ValueError, match="unknown evidence capability"):
        execute_evidence_request(
            request,
            ExplodingStore(),
            provider=lambda _request: pytest.fail("provider must not run"),
            captured_at=CAPTURED_AT,
        )


def test_invalid_capability_parameters_are_rejected_before_motivation_lookup(tmp_path):
    from episteme.evidence_request import EvidenceRequest, execute_evidence_request

    request = EvidenceRequest(
        capability="crossref_works",
        parameters={"rows": 1001},
        rationale="Discriminate the current candidate hypotheses.",
        requested_representation="application/json",
        motivation_ids=("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",),
    )

    class ExplodingStore:
        def epistemic_object_exists(self, _object_id):
            raise AssertionError(
                "motivation lookup must not occur before capability request validation"
            )

    with pytest.raises(ValueError, match="rows"):
        execute_evidence_request(
            request,
            ExplodingStore(),
            provider=lambda _request: pytest.fail("provider must not run"),
            captured_at=CAPTURED_AT,
        )


def test_completed_evidence_capture_does_not_create_grounded_record(tmp_path):
    from episteme.evidence_request import EvidenceRequest, execute_evidence_request

    motivation_id = "abababab-abab-4aba-8aba-abababababab"
    request = EvidenceRequest(
        capability="crossref_works",
        parameters={"rows": 1},
        rationale="Acquire external material without promoting it to grounded knowledge.",
        requested_representation="application/json",
        motivation_ids=(motivation_id,),
    )

    with Store(tmp_path / "phase28.sqlite", capture_root=tmp_path / "captures") as store:
        _seed_motivation(store, motivation_id)
        result = execute_evidence_request(
            request,
            store,
            provider=lambda _request: AcquisitionResponse(
                status=200,
                media_type="application/json",
                source_version="v1",
                content=CONTENT,
                outcome=CaptureOutcome.COMPLETE,
            ),
            captured_at=CAPTURED_AT,
            capture_id="capture-phase28-no-grounding",
        )

        assert result.outcome is CaptureOutcome.COMPLETE
        assert store.get_captured_representation(result.id) is not None
        assert list(store.iter_records()) == [
            store.get_record(motivation_id)
        ]


def test_host_acquisition_parameters_cannot_be_mutated_by_provider(tmp_path):
    from episteme.evidence_request import EvidenceRequest, execute_evidence_request

    motivation_id = "cdcdcdcd-cdcd-4cdc-8cdc-cdcdcdcdcdcd"
    request = EvidenceRequest(
        capability="crossref_works",
        parameters={"rows": 1},
        rationale="Keep host-owned acquisition parameters stable through execution.",
        requested_representation="application/json",
        motivation_ids=(motivation_id,),
    )

    def provider(acquisition):
        with pytest.raises(TypeError):
            acquisition.request_parameters["rows"] = 999
        return AcquisitionResponse(
            status=200,
            media_type="application/json",
            source_version="v1",
            content=CONTENT,
            outcome=CaptureOutcome.COMPLETE,
        )

    with Store(tmp_path / "phase28.sqlite", capture_root=tmp_path / "captures") as store:
        _seed_motivation(store, motivation_id)
        result = execute_evidence_request(
            request,
            store,
            provider=provider,
            captured_at=CAPTURED_AT,
            capture_id="capture-phase28-frozen-acquisition-params",
        )

        assert result.request_parameters == {"rows": 1}


def test_captured_representation_request_parameters_cannot_be_mutated(tmp_path):
    from episteme.evidence_request import EvidenceRequest, execute_evidence_request

    motivation_id = "cececece-cece-4ece-8ece-cececececece"
    request = EvidenceRequest(
        capability="crossref_works",
        parameters={"rows": 1},
        rationale="Preserve immutable acquisition provenance after capture.",
        requested_representation="application/json",
        motivation_ids=(motivation_id,),
    )

    with Store(tmp_path / "phase28.sqlite", capture_root=tmp_path / "captures") as store:
        _seed_motivation(store, motivation_id)
        result = execute_evidence_request(
            request,
            store,
            provider=lambda _request: AcquisitionResponse(
                status=200,
                media_type="application/json",
                source_version="v1",
                content=CONTENT,
                outcome=CaptureOutcome.COMPLETE,
            ),
            captured_at=CAPTURED_AT,
            capture_id="capture-phase28-frozen-capture-params",
        )

        with pytest.raises(TypeError):
            result.request_parameters["rows"] = 999

        assert result.request_parameters == {"rows": 1}


def test_reloaded_capture_request_parameters_remain_immutable(tmp_path):
    from episteme.evidence_request import EvidenceRequest, execute_evidence_request

    motivation_id = "ceeeeeee-ceee-4eee-8eee-ceeeeeeeeeee"
    request = EvidenceRequest(
        capability="crossref_works",
        parameters={"rows": 1},
        rationale="Preserve immutable acquisition provenance across reload.",
        requested_representation="application/json",
        motivation_ids=(motivation_id,),
    )

    db_path = tmp_path / "phase28.sqlite"
    capture_root = tmp_path / "captures"
    with Store(db_path, capture_root=capture_root) as store:
        _seed_motivation(store, motivation_id)
        result = execute_evidence_request(
            request,
            store,
            provider=lambda _request: AcquisitionResponse(
                status=200,
                media_type="application/json",
                source_version="v1",
                content=CONTENT,
                outcome=CaptureOutcome.COMPLETE,
            ),
            captured_at=CAPTURED_AT,
            capture_id="capture-phase28-reloaded-params",
        )
        assert result.request_parameters == {"rows": 1}

    with Store(db_path, capture_root=capture_root) as store:
        reloaded = store.get_captured_representation(
            "capture-phase28-reloaded-params"
        )
        assert reloaded is not None
        with pytest.raises(TypeError):
            reloaded.request_parameters["rows"] = 999
        assert reloaded.request_parameters == {"rows": 1}



def test_nested_acquisition_request_parameters_cannot_be_mutated():
    request = AcquisitionRequest(
        source_id="test-source",
        requested_resource="test-resource",
        request_parameters={"nested": {"limit": 10}},
        acquisition_method="test",
        acquisition_method_version="1",
    )

    with pytest.raises(TypeError):
        request.request_parameters["nested"]["limit"] = 999

    assert request.request_parameters["nested"]["limit"] == 10


def test_nested_evidence_request_parameters_cannot_be_mutated():
    from episteme.evidence_request import EvidenceRequest

    request = EvidenceRequest(
        capability="crossref_works",
        parameters={"nested": {"limit": 10}},
        rationale="Keep planner-owned request parameters immutable.",
        requested_representation="application/json",
        motivation_ids=("ffffffff-ffff-4fff-8fff-ffffffffffff",),
    )

    with pytest.raises(TypeError):
        request.parameters["nested"]["limit"] = 999

    assert request.parameters["nested"]["limit"] == 10
