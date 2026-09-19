"""Phase 9 proof of structural-gap discovery."""

from episteme import (
    DiscoveryFindingKind,
    Provenance,
    Record,
    RecordKind,
    Store,
    detect_structural_sequence_gap,
    make_relationship,
)

CREATED = "2026-09-19T00:00:00Z"
PROVENANCE = (
    Provenance(
        source_id="phase9-structural-fixture",
        captured_at=CREATED,
        source_location="https://example.org/phase9",
        source_version="1",
    ),
)


def test_structural_sequence_gap_requires_explicit_structure():
    records = tuple(
        Record(
            id=f"{index:08d}-0000-4000-8000-000000000000",
            kind=RecordKind.OBSERVATION,
            payload={"position": index},
            provenance=PROVENANCE,
            created_at=CREATED,
        )
        for index in range(1, 4)
    )

    with Store() as store:
        for record in records:
            store.put_record(record)

        relationship = make_relationship(
            subject_id=records[0].id,
            predicate="next",
            object_id=records[1].id,
            provenance=PROVENANCE,
            created_at=CREATED,
        )
        store.put_relationship(relationship)

        gap = detect_structural_sequence_gap(
            store,
            ordered_ids=tuple(record.id for record in records),
            predicate="next",
            created_at="2026-09-19T00:01:00Z",
        )

    assert gap is not None
    assert gap.kind is DiscoveryFindingKind.GAP
    assert gap.input_ids == tuple(record.id for record in records)
    assert gap.expectation == (records[1].id, "next", records[2].id)
    assert gap.context_ids == ()
    assert "explicit ordered structure" in gap.rationale
