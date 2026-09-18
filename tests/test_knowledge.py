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
