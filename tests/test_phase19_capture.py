"""Phase 19 proof of filesystem-backed captured representations."""

import hashlib

import pytest

from episteme import CaptureOutcome, CapturedRepresentation, Store


CAPTURE_ID = "capture-phase19-1"
CREATED = "2026-09-20T00:00:00Z"
CONTENT = b'{"message":{"items":[{"DOI":"10.1234/example"}]}}'
DIGEST = hashlib.sha256(CONTENT).hexdigest()


def _capture():
    return CapturedRepresentation(
        id=CAPTURE_ID,
        source_id="crossref",
        requested_resource="https://api.crossref.org/works",
        request_parameters={"query": "example"},
        captured_at=CREATED,
        response_status=200,
        media_type="application/json",
        source_version="2026-09-20",
        content_digest=DIGEST,
        content_reference=f"sha256/{DIGEST}",
        acquisition_method="http",
        acquisition_method_version="1",
        outcome=CaptureOutcome.COMPLETE,
    )


def test_filesystem_capture_round_trip_and_digest_verification(tmp_path):
    db = tmp_path / "phase19.sqlite"
    root = tmp_path / "captures"
    capture = _capture()

    with Store(db, capture_root=root) as store:
        store.put_captured_representation(capture, CONTENT)

    assert (root / f"sha256/{DIGEST}").read_bytes() == CONTENT

    with Store(db, read_only=True, capture_root=root) as store:
        assert store.get_captured_representation(CAPTURE_ID) == capture
        assert list(store.iter_captured_representations()) == [capture]
        assert store.read_captured_content(CAPTURE_ID) == CONTENT


def test_capture_identity_is_append_only(tmp_path):
    db = tmp_path / "phase19.sqlite"
    root = tmp_path / "captures"
    capture = _capture()

    with Store(db, capture_root=root) as store:
        store.put_captured_representation(capture, CONTENT)
        with pytest.raises(ValueError, match="already exists"):
            store.put_captured_representation(capture, CONTENT)


def test_failed_capture_has_no_content(tmp_path):
    db = tmp_path / "phase19.sqlite"
    failure = CapturedRepresentation(
        id="capture-phase19-failed",
        source_id="example",
        requested_resource="https://example.org/missing",
        request_parameters={},
        captured_at=CREATED,
        response_status=404,
        media_type=None,
        source_version=None,
        content_digest=None,
        content_reference=None,
        acquisition_method="http",
        acquisition_method_version="1",
        outcome=CaptureOutcome.FAILED,
        error="HTTP 404: not found",
    )

    with Store(db) as store:
        store.put_captured_representation(failure)
        assert store.get_captured_representation(failure.id) == failure


def test_identical_content_can_be_reused_by_distinct_captures(tmp_path):
    db = tmp_path / "phase19.sqlite"
    root = tmp_path / "captures"
    first = _capture()
    second = CapturedRepresentation(
        id="capture-phase19-2",
        source_id="crossref",
        requested_resource=first.requested_resource,
        request_parameters=first.request_parameters,
        captured_at=CREATED,
        response_status=200,
        media_type=first.media_type,
        source_version=first.source_version,
        content_digest=first.content_digest,
        content_reference=first.content_reference,
        acquisition_method=first.acquisition_method,
        acquisition_method_version=first.acquisition_method_version,
        outcome=CaptureOutcome.COMPLETE,
    )

    with Store(db, capture_root=root) as store:
        store.put_captured_representation(first, CONTENT)
        store.put_captured_representation(second, CONTENT)
        assert list(store.iter_captured_representations()) == [first, second]


def test_partial_capture_remains_partial(tmp_path):
    db = tmp_path / "phase19.sqlite"
    root = tmp_path / "captures"
    partial_content = b'partial'
    digest = hashlib.sha256(partial_content).hexdigest()
    capture = CapturedRepresentation(
        id="capture-phase19-partial",
        source_id="example",
        requested_resource="https://example.org/stream",
        request_parameters={},
        captured_at=CREATED,
        response_status=206,
        media_type="application/octet-stream",
        source_version=None,
        content_digest=digest,
        content_reference=f"sha256/{digest}",
        acquisition_method="http",
        acquisition_method_version="1",
        outcome=CaptureOutcome.PARTIAL,
    )

    with Store(db, capture_root=root) as store:
        store.put_captured_representation(capture, partial_content)
        assert store.get_captured_representation(capture.id).outcome is CaptureOutcome.PARTIAL
        assert store.read_captured_content(capture.id) == partial_content


def test_corrupted_capture_content_is_rejected_on_read(tmp_path):
    db = tmp_path / "phase19.sqlite"
    root = tmp_path / "captures"
    capture = _capture()

    with Store(db, capture_root=root) as store:
        store.put_captured_representation(capture, CONTENT)

    (root / capture.content_reference).write_bytes(b"tampered")

    with Store(db, read_only=True, capture_root=root) as store:
        with pytest.raises(ValueError, match="digest mismatch"):
            store.read_captured_content(capture.id)


def test_capture_storage_does_not_create_grounded_source_record(tmp_path):
    db = tmp_path / "phase19.sqlite"
    root = tmp_path / "captures"
    capture = _capture()

    with Store(db, capture_root=root) as store:
        store.put_captured_representation(capture, CONTENT)
        assert list(store.iter_records()) == []
