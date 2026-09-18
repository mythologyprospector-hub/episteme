from episteme import (
    Provenance,
    RecordKind,
    Store,
    canonical_json,
    make_record,
    make_relationship,
)


def provenance() -> Provenance:
    return Provenance(
        source_id="source:example",
        source_location="https://example.test/source",
        source_version="1",
        captured_at="2026-09-18T00:00:00Z",
    )


def test_record_requires_provenance():
    try:
        make_record(
            RecordKind.OBSERVATION,
            {"value": 42},
            (),
            "2026-09-18T00:00:00Z",
        )
    except ValueError as exc:
        assert "provenance" in str(exc)
    else:
        raise AssertionError("record without provenance was accepted")


def test_canonical_json_is_deterministic():
    assert canonical_json({"b": 2, "a": 1}) == '{"a":1,"b":2}'


def test_store_round_trip_for_record():
    record = make_record(
        RecordKind.OBSERVATION,
        {"value": 42, "unit": "arbitrary"},
        (provenance(),),
        "2026-09-18T00:00:01Z",
    )

    with Store() as store:
        store.put_record(record)
        restored = store.get_record(record.id)

    assert restored == record


def test_store_round_trip_for_relationship():
    first = make_record(
        RecordKind.OBSERVATION,
        {"value": 1},
        (provenance(),),
        "2026-09-18T00:00:01Z",
    )
    second = make_record(
        RecordKind.OBSERVATION,
        {"value": 2},
        (provenance(),),
        "2026-09-18T00:00:02Z",
    )

    with Store() as store:
        store.put_record(first)
        store.put_record(second)
        relationship = make_relationship(
            first.id,
            "precedes",
            second.id,
            (provenance(),),
            "2026-09-18T00:00:03Z",
        )
        store.put_relationship(relationship)
        restored = store.get_relationship(relationship.id)

    assert restored == relationship


def test_relationship_cannot_reference_missing_record():
    first = make_record(
        RecordKind.OBSERVATION,
        {"value": 1},
        (provenance(),),
        "2026-09-18T00:00:01Z",
    )

    relationship = make_relationship(
        first.id,
        "precedes",
        "00000000-0000-0000-0000-000000000000",
        (provenance(),),
        "2026-09-18T00:00:02Z",
    )

    with Store() as store:
        store.put_record(first)
        try:
            store.put_relationship(relationship)
        except ValueError as exc:
            assert "missing record" in str(exc)
        else:
            raise AssertionError("dangling relationship was accepted")


def test_identical_payloads_keep_distinct_identity():
    first = make_record(
        RecordKind.OBSERVATION,
        {"value": 42},
        (provenance(),),
        "2026-09-18T00:00:01Z",
    )
    second = make_record(
        RecordKind.OBSERVATION,
        {"value": 42},
        (provenance(),),
        "2026-09-18T00:00:02Z",
    )

    assert first.id != second.id



def test_jsonl_ingestion_preserves_grounded_records(tmp_path):
    from episteme import ingest_jsonl_file

    fixture = tmp_path / "sample.jsonl"
    fixture.write_text(
        '{"id":"11111111-1111-4111-8111-111111111111","kind":"observation","payload":{"value":42},"provenance":[{"source_id":"example:source","captured_at":"2026-09-18T00:00:00Z"}],"created_at":"2026-09-18T00:00:00Z","schema_version":1}\n',
        encoding="utf-8",
    )

    with Store() as store:
        assert ingest_jsonl_file(fixture, store) == 1
        record = store.get_record("11111111-1111-4111-8111-111111111111")

    assert record is not None
    assert record.kind is RecordKind.OBSERVATION
    assert record.payload["value"] == 42


def test_jsonl_ingestion_rejects_malformed_record(tmp_path):
    from episteme import ingest_jsonl_file

    fixture = tmp_path / "bad.jsonl"
    fixture.write_text('{"kind":"observation"}\n', encoding="utf-8")

    with Store() as store:
        try:
            ingest_jsonl_file(fixture, store)
        except ValueError as exc:
            assert "line 1" in str(exc)
        else:
            raise AssertionError("malformed record was accepted")
