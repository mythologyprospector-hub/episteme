from episteme import RecordKind, Store
from episteme.public_import import import_crossref_works


CAPTURED_AT = "2026-09-18T14:00:00+00:00"


def _crossref_item():
    return {
        "DOI": "10.1234/example.1",
        "title": ["A scientific work"],
        "author": [{"given": "Ada", "family": "Example"}],
        "type": "journal-article",
        "abstract": "A source-provided abstract.",
        "issued": {"date-parts": [[2024, 5, 1]]},
    }


def test_crossref_import_preserves_source_metadata_as_source_record():
    store = Store()
    count = import_crossref_works(
        {"message": {"items": [_crossref_item()]}},
        store,
        captured_at=CAPTURED_AT,
    )

    assert count == 1
    record = next(store.iter_records())
    assert record.kind is RecordKind.SOURCE
    assert record.payload["external_format"] == "crossref-work"
    assert record.payload["work"]["abstract"] == "A source-provided abstract."
    assert record.provenance[0].source_id == "crossref:10.1234/example.1"
    assert record.provenance[0].source_location == "https://doi.org/10.1234/example.1"
    assert record.provenance[0].captured_at == CAPTURED_AT
    assert record.provenance[0].source_version == "[2024, 5, 1]"
    assert "scientific claim" not in record.payload


def test_crossref_import_is_deterministic_for_record_identity():
    data = {"message": {"items": [_crossref_item()]}}
    store = Store()
    import_crossref_works(data, store, captured_at=CAPTURED_AT)
    first = next(store.iter_records())

    other = Store()
    import_crossref_works(data, other, captured_at="2026-09-19T14:00:00+00:00")
    second = next(other.iter_records())

    assert first.id == second.id
    assert first.payload == second.payload


def test_crossref_import_rejects_missing_doi_without_repair():
    store = Store()
    item = {"title": ["No DOI"]}
    try:
        import_crossref_works(
            {"message": {"items": [item]}},
            store,
            captured_at=CAPTURED_AT,
        )
    except ValueError as exc:
        assert "requires a DOI" in str(exc)
    else:
        raise AssertionError("missing DOI should be rejected")


def test_crossref_import_validates_entire_batch_before_persistence():
    store = Store()
    valid = _crossref_item()
    invalid = {"title": ["No DOI"]}

    try:
        import_crossref_works(
            {"message": {"items": [valid, invalid]}},
            store,
            captured_at=CAPTURED_AT,
        )
    except ValueError as exc:
        assert "requires a DOI" in str(exc)
    else:
        raise AssertionError("invalid batch should be rejected")

    assert list(store.iter_records()) == []


def test_crossref_reimport_cannot_overwrite_immutable_record():
    import sqlite3

    store = Store()
    original = _crossref_item()
    import_crossref_works(
        {"message": {"items": [original]}},
        store,
        captured_at=CAPTURED_AT,
    )
    before = next(store.iter_records())

    changed = dict(original)
    changed["title"] = ["A changed title"]
    try:
        import_crossref_works(
            {"message": {"items": [changed]}},
            store,
            captured_at="2026-09-19T14:00:00+00:00",
        )
    except sqlite3.IntegrityError:
        pass
    else:
        raise AssertionError("re-import should not overwrite an immutable record")

    after = store.get_record(before.id)
    assert after == before
