"""Phase 10 proof of candidate completion boundaries."""

import pytest

from episteme import (
    DiscoveryFindingKind,
    DiscoveryExpectationKind,
    Provenance,
    Record,
    RecordKind,
    Store,
    complete_structural_gap,
    detect_positional_gap,
)

CREATED = "2026-09-19T00:00:00Z"
PROVENANCE = (
    Provenance(
        source_id="phase10-candidate-fixture",
        captured_at=CREATED,
        source_location="https://example.org/phase10",
        source_version="1",
    ),
)


def _fixture():
    return tuple(
        Record(
            id=f"aaaaaaaa-{index:04d}-4aaa-8aaa-aaaaaaaaaaaa",
            kind=RecordKind.OBSERVATION,
            payload={"position": position},
            provenance=PROVENANCE,
            created_at=CREATED,
        )
        for index, position in enumerate((1.0, 2.0, 4.0), start=1)
    )


def test_candidate_completion_is_downstream_of_established_gap():
    records = _fixture()

    with Store() as store:
        for record in records:
            store.put_record(record)
        gap = detect_positional_gap(
            store,
            record_ids=tuple(record.id for record in records),
            position_key="position",
            step=1.0,
            created_at="2026-09-19T00:01:00Z",
        )
        assert gap is not None
        store.put_discovery_finding(gap)

        candidate = complete_structural_gap(
            store,
            gap_id=gap.id,
            statement="The missing occupant has position 3.0.",
            method="phase10-fixture-candidate",
            method_version="1",
            rationale="This candidate explicitly proposes an occupant for the established positional gap.",
            assumptions=("the declared unit step remains applicable",),
            created_at="2026-09-19T00:02:00Z",
        )

        assert candidate.finding_ids == (gap.id,)
        assert candidate.input_ids == gap.input_ids
        assert candidate.assumptions == ("the declared unit step remains applicable",)
        assert store.get_discovery_finding(gap.id) == gap

        store.put_hypothesis(candidate)
        persisted = store.get_hypothesis(candidate.id)

    assert persisted == candidate


def test_candidate_completion_requires_gap_not_arbitrary_finding():
    records = _fixture()

    with Store() as store:
        for record in records:
            store.put_record(record)
        gap = detect_positional_gap(
            store,
            record_ids=tuple(record.id for record in records),
            position_key="position",
            step=1.0,
            created_at="2026-09-19T00:03:00Z",
        )
        assert gap is not None
        store.put_discovery_finding(gap)

        with pytest.raises(ValueError, match="requires a gap finding"):
            complete_structural_gap(
                store,
                gap_id=records[0].id,
                statement="Not a valid downstream candidate.",
                method="test",
                method_version="1",
                rationale="test",
                created_at="2026-09-19T00:04:00Z",
            )


def test_candidate_completion_does_not_create_evidence_or_change_gap():
    records = _fixture()

    with Store() as store:
        for record in records:
            store.put_record(record)
        gap = detect_positional_gap(
            store,
            record_ids=tuple(record.id for record in records),
            position_key="position",
            step=1.0,
            created_at="2026-09-19T00:05:00Z",
        )
        assert gap is not None
        store.put_discovery_finding(gap)
        before = gap.to_dict()

        candidate = complete_structural_gap(
            store,
            gap_id=gap.id,
            statement="A proposed occupant for the missing position.",
            method="test-candidate",
            method_version="1",
            rationale="Candidate generation is downstream of the established gap.",
            created_at="2026-09-19T00:06:00Z",
        )
        store.put_hypothesis(candidate)

        after = store.get_discovery_finding(gap.id)
        grounded = [store.get_record(record.id) for record in records]

    assert after is not None
    assert after.to_dict() == before
    assert all(record is not None for record in grounded)
    assert candidate.finding_ids == (gap.id,)
    assert candidate.input_ids == gap.input_ids
