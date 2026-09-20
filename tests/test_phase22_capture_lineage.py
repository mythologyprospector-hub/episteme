"""Phase 22 proof of capture-to-grounded provenance lineage."""

import json

import pytest

from episteme import (
    CaptureOutcome,
    CapturedRepresentation,
    Provenance,
    RecordKind,
    Store,
)
from episteme.public_import import import_crossref_works


CREATED = "2026-09-20T00:00:00Z"
CAPTURE_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


def _capture(store: Store, payload: bytes) -> None:
    import hashlib

    digest = hashlib.sha256(payload).hexdigest()
    store.put_captured_representation(
        CapturedRepresentation(
            id=CAPTURE_ID,
            source_id="crossref",
            requested_resource="https://api.crossref.org/v1/works",
            request_parameters={"rows": 1},
            captured_at=CREATED,
            response_status=200,
            media_type="application/json",
            source_version="etag-1",
            content_digest=digest,
            content_reference=f"sha256/{digest}",
            acquisition_method="crossref-rest",
            acquisition_method_version="1",
            outcome=CaptureOutcome.COMPLETE,
        ),
        content=payload,
    )


def test_crossref_import_can_preserve_exact_capture_identity(tmp_path):
    with Store(tmp_path / "episteme.sqlite", capture_root=tmp_path / "captures") as store:
        data = {
            "message": {
                "items": [
                    {
                        "DOI": "10.1234/example",
                        "title": ["A captured work"],
                        "created": {"date-parts": [[2026, 9, 20]]},
                    }
                ]
            }
        }
        payload = json.dumps(data, separators=(",", ":")).encode()
        _capture(store, payload)

        assert import_crossref_works(
            data,
            store,
            captured_at=CREATED,
            capture_id=CAPTURE_ID,
        ) == 1

        record = next(store.iter_records(kind=RecordKind.SOURCE.value))
        assert record.provenance[0].capture_id == CAPTURE_ID
        recovered = Provenance.from_dict(record.provenance[0].to_dict())
        assert recovered == record.provenance[0]

    with Store(tmp_path / "episteme.sqlite", capture_root=tmp_path / "captures") as store:
        recovered_record = next(store.iter_records(kind=RecordKind.SOURCE.value))
        assert recovered_record.provenance[0].capture_id == CAPTURE_ID



def test_crossref_import_rejects_data_that_does_not_match_capture(tmp_path):
    with Store(tmp_path / "episteme.sqlite", capture_root=tmp_path / "captures") as store:
        captured = {"message": {"items": []}}
        _capture(store, json.dumps(captured, separators=(",", ":")).encode())
        with pytest.raises(ValueError, match="does not match captured representation"):
            import_crossref_works(
                {"message": {"items": [{"DOI": "10.1234/different"}]}},
                store,
                captured_at=CREATED,
                capture_id=CAPTURE_ID,
            )
        assert list(store.iter_records()) == []


def test_crossref_import_rejects_missing_capture_lineage(tmp_path):
    with Store(tmp_path / "episteme.sqlite", capture_root=tmp_path / "captures") as store:
        with pytest.raises(ValueError, match="missing capture"):
            import_crossref_works(
                {"message": {"items": []}},
                store,
                captured_at=CREATED,
                capture_id=CAPTURE_ID,
            )


def test_provenance_capture_identity_is_optional_for_existing_records():
    provenance = Provenance(source_id="existing", captured_at=CREATED)
    assert provenance.capture_id is None
    assert "capture_id" not in provenance.to_dict()
