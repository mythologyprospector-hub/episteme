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
    )

    with Store(db) as store:
        store.put_captured_representation(failure)
        assert store.get_captured_representation(failure.id) == failure
