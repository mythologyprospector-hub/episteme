from episteme import RecordKind, Store
from episteme.praxis_import import import_praxis_evidence_handoff


CAPTURED_AT = "2026-10-03T16:00:00+00:00"


def _handoff():
    return {
        "schema_version": 1,
        "record_kind": "result",
        "source_id": "praxis:test-source",
        "captured_at": CAPTURED_AT,
        "source_location": "https://example.test/result/1",
        "praxis_evidence": {
            "id": "evidence:result-1",
            "statement": "The observed result was reproducible.",
            "provenance": "test recorder",
            "uncertainty": "limited sample",
            "source_result_id": "result-1",
        },
        "praxis_admission": {
            "problem_id": "problem-1",
            "evidence_item_id": "evidence:result-1",
        },
    }


def test_praxis_handoff_becomes_grounded_record_without_merging_identity():
    store = Store()
    record = import_praxis_evidence_handoff(_handoff(), store)

    assert record.kind is RecordKind.RESULT
    assert record.id != _handoff()["praxis_evidence"]["id"]
    assert record.payload["praxis_evidence"]["id"] == "evidence:result-1"
    assert record.payload["praxis_admission"]["problem_id"] == "problem-1"
    assert record.provenance[0].source_id == "praxis:test-source"
    assert record.provenance[0].captured_at == CAPTURED_AT


def test_praxis_handoff_does_not_infer_record_kind():
    data = _handoff()
    data["record_kind"] = "not-a-record-kind"

    try:
        import_praxis_evidence_handoff(data, Store())
    except ValueError as exc:
        assert "RecordKind" in str(exc)
    else:
        raise AssertionError("invalid record kind should be rejected")


def test_praxis_handoff_requires_explicit_provenance_inputs():
    for field in ("source_id", "captured_at"):
        data = _handoff()
        data[field] = ""
        try:
            import_praxis_evidence_handoff(data, Store())
        except ValueError as exc:
            assert field in str(exc)
        else:
            raise AssertionError(f"{field} should be required")


def test_praxis_handoff_rejects_missing_nested_material():
    for field in ("praxis_evidence", "praxis_admission"):
        data = _handoff()
        data.pop(field)
        try:
            import_praxis_evidence_handoff(data, Store())
        except ValueError as exc:
            assert field in str(exc)
        else:
            raise AssertionError(f"{field} should be required")
