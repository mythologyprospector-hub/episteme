"""Phase 20 proof of bounded external acquisition."""

import json

from episteme import (
    AcquisitionRequest,
    AcquisitionResponse,
    CaptureOutcome,
    Store,
    acquire,
    import_crossref_works,
)


CONTENT = b'{"message":{"items":[{"DOI":"10.1234/example","title":["Example"]}]}}'
CAPTURED_AT = "2026-09-20T12:00:00Z"


def _request():
    return AcquisitionRequest(
        source_id="crossref",
        requested_resource="https://api.crossref.org/v1/works",
        request_parameters={"rows": 1, "query.title": "example"},
        acquisition_method="test-provider",
        acquisition_method_version="1",
    )


def test_acquire_persists_successful_response_without_creating_source(tmp_path):
    db = tmp_path / "phase20.sqlite"
    root = tmp_path / "captures"

    def provider(request):
        assert request is not None
        return AcquisitionResponse(
            status=200,
            media_type="application/json",
            source_version="etag-example",
            content=CONTENT,
            outcome=CaptureOutcome.COMPLETE,
        )

    with Store(db, capture_root=root) as store:
        capture = acquire(
            _request(),
            provider,
            store,
            captured_at=CAPTURED_AT,
            capture_id="capture-phase20-success",
        )
        assert capture.outcome is CaptureOutcome.COMPLETE
        assert store.read_captured_content(capture.id) == CONTENT
        assert list(store.iter_records()) == []


def test_acquire_persists_provider_failure(tmp_path):
    db = tmp_path / "phase20.sqlite"

    def provider(request):
        raise TimeoutError("provider timed out")

    with Store(db) as store:
        capture = acquire(
            _request(),
            provider,
            store,
            captured_at=CAPTURED_AT,
            capture_id="capture-phase20-failed",
        )
        assert capture.outcome is CaptureOutcome.FAILED
        assert capture.error == "TimeoutError: provider timed out"
        assert capture.content_reference is None
        assert store.get_captured_representation(capture.id) == capture


def test_captured_crossref_response_flows_through_existing_adapter(tmp_path):
    db = tmp_path / "phase20.sqlite"
    root = tmp_path / "captures"

    def provider(request):
        return AcquisitionResponse(
            status=200,
            media_type="application/json",
            source_version="etag-example",
            content=CONTENT,
            outcome=CaptureOutcome.COMPLETE,
        )

    with Store(db, capture_root=root) as store:
        capture = acquire(
            _request(),
            provider,
            store,
            captured_at=CAPTURED_AT,
            capture_id="capture-phase20-adapter",
        )
        payload = json.loads(store.read_captured_content(capture.id))
        assert import_crossref_works(
            payload,
            store,
            captured_at=CAPTURED_AT,
            source_location=capture.requested_resource,
        ) == 1
        assert len(list(store.iter_records())) == 1


def test_crossref_request_is_bounded_to_versioned_works_endpoint(monkeypatch):
    from episteme.providers import crossref

    seen = {}

    class FakeHeaders:
        def get_content_type(self):
            return "application/json"

        def get(self, name):
            return "etag-example" if name == "ETag" else None

    class FakeResponse:
        status = 200
        headers = FakeHeaders()

        def read(self):
            return CONTENT

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        seen["user_agent"] = request.get_header("User-agent")
        seen["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(crossref, "urlopen", fake_urlopen)

    response = crossref.fetch_works(
        AcquisitionRequest(
            source_id="crossref",
            requested_resource="https://api.crossref.org/v1/works",
            request_parameters={"rows": 1, "mailto": "example@example.org"},
            acquisition_method=crossref.CROSSREF_ACQUISITION_METHOD,
            acquisition_method_version=crossref.CROSSREF_ACQUISITION_METHOD_VERSION,
        ),
        timeout=7,
    )

    assert response.status == 200
    assert response.outcome is CaptureOutcome.COMPLETE
    assert "rows=1" in seen["url"]
    assert "mailto=example%40example.org" in seen["url"]
    assert seen["user_agent"] == crossref.USER_AGENT
    assert seen["timeout"] == 7


def test_acquire_persists_partial_response_as_partial(tmp_path):
    db = tmp_path / "phase20.sqlite"
    root = tmp_path / "captures"

    def provider(request):
        return AcquisitionResponse(
            status=206,
            media_type="application/json",
            source_version="etag-partial",
            content=CONTENT,
            outcome=CaptureOutcome.PARTIAL,
        )

    with Store(db, capture_root=root) as store:
        capture = acquire(
            _request(),
            provider,
            store,
            captured_at=CAPTURED_AT,
            capture_id="capture-phase20-partial",
        )
        assert capture.outcome is CaptureOutcome.PARTIAL
        assert capture.content_reference is not None
        assert store.read_captured_content(capture.id) == CONTENT


def test_repeated_acquisition_events_remain_distinct_with_identical_content(tmp_path):
    db = tmp_path / "phase20.sqlite"
    root = tmp_path / "captures"

    def provider(request):
        return AcquisitionResponse(
            status=200,
            media_type="application/json",
            source_version="etag-example",
            content=CONTENT,
            outcome=CaptureOutcome.COMPLETE,
        )

    with Store(db, capture_root=root) as store:
        first = acquire(
            _request(),
            provider,
            store,
            captured_at=CAPTURED_AT,
            capture_id="capture-phase20-repeat-1",
        )
        second = acquire(
            _request(),
            provider,
            store,
            captured_at="2026-09-20T12:00:01Z",
            capture_id="capture-phase20-repeat-2",
        )

        assert first.id != second.id
        assert first.content_digest == second.content_digest
        assert first.content_reference == second.content_reference
        assert [capture.id for capture in store.iter_captured_representations()] == [
            first.id,
            second.id,
        ]
