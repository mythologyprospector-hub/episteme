"""Phase 10 proof of the candidate constraint-assessment boundary."""

from uuid import uuid4

import pytest

from episteme import (
    CandidateConstraintAssessment,
    CandidateConstraintStatus,
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
        source_id="phase10-assessment-fixture",
        captured_at=CREATED,
        source_location="https://example.org/phase10-assessment",
        source_version="1",
    ),
)


def _records():
    return tuple(
        Record(
            id=str(uuid4()),
            kind=RecordKind.OBSERVATION,
            payload={"position": position},
            provenance=PROVENANCE,
            created_at=CREATED,
        )
        for position in (1.0, 2.0, 4.0)
    )


def _candidate(store, records):
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
        statement="A proposed occupant exists at position 3.0.",
        method="phase10-assessment-candidate",
        method_version="1",
        rationale="Candidate generation follows an established gap.",
        assumptions=("the declared unit step remains applicable",),
        created_at="2026-09-19T00:02:00Z",
    )
    store.put_hypothesis(candidate)
    return gap, candidate


def test_constraint_assessment_has_explicit_status_and_roundtrips():
    records = _records()
    with Store() as store:
        gap, candidate = _candidate(store, records)
        assessment = CandidateConstraintAssessment(
            id=str(uuid4()),
            candidate_id=candidate.id,
            constraint_id="positional-gap:3.0",
            basis="Established positional gap at position 3.0.",
            status=CandidateConstraintStatus.SATISFIED,
            input_ids=gap.input_ids,
            assumptions=("the declared unit step remains applicable",),
            explanation="The candidate places the proposed occupant at the required position.",
            method="phase10-constraint-assessment",
            method_version="1",
            created_at="2026-09-19T00:03:00Z",
        )
        store.put_candidate_constraint_assessment(assessment)
        persisted = store.get_candidate_constraint_assessment(assessment.id)

    assert persisted == assessment
    assert persisted is not None
    assert persisted.status is CandidateConstraintStatus.SATISFIED
    assert persisted.to_dict()["status"] == "satisfied"


def test_constraint_assessment_preserves_all_three_statuses_without_a_score():
    statuses = (
        CandidateConstraintStatus.SATISFIED,
        CandidateConstraintStatus.VIOLATED,
        CandidateConstraintStatus.UNRESOLVED,
    )
    assert {status.value for status in statuses} == {
        "satisfied",
        "violated",
        "unresolved",
    }
    assert all("score" not in status.value for status in statuses)


def test_constraint_assessment_requires_existing_candidate_and_grounded_inputs():
    records = _records()
    with Store() as store:
        gap, candidate = _candidate(store, records)
        base = {
            "candidate_id": candidate.id,
            "constraint_id": "constraint-1",
            "basis": "Explicit structural basis.",
            "status": CandidateConstraintStatus.UNRESOLVED,
            "input_ids": gap.input_ids,
            "assumptions": (),
            "explanation": "The available representation does not determine this yet.",
            "method": "phase10-test",
            "method_version": "1",
            "created_at": "2026-09-19T00:04:00Z",
        }
        with pytest.raises(ValueError, match="missing candidate"):
            store.put_candidate_constraint_assessment(
                CandidateConstraintAssessment(id=str(uuid4()), **{**base, "candidate_id": str(uuid4())})
            )
        with pytest.raises(ValueError, match="missing input"):
            store.put_candidate_constraint_assessment(
                CandidateConstraintAssessment(
                    id=str(uuid4()),
                    **{**base, "input_ids": (str(uuid4()),)},
                )
            )


def test_constraint_assessment_is_queryable_by_candidate():
    records = _records()
    with Store() as store:
        gap, candidate = _candidate(store, records)
        assessments = []
        for index, status in enumerate(
            (
                CandidateConstraintStatus.SATISFIED,
                CandidateConstraintStatus.VIOLATED,
                CandidateConstraintStatus.UNRESOLVED,
            )
        ):
            assessment = CandidateConstraintAssessment(
                id=str(uuid4()),
                candidate_id=candidate.id,
                constraint_id=f"constraint-{index}",
                basis=f"Explicit structural basis {index}.",
                status=status,
                input_ids=gap.input_ids,
                assumptions=(),
                explanation=f"Assessment {index}.",
                method="phase10-test",
                method_version="1",
                created_at=f"2026-09-19T00:0{4 + index}:00Z",
            )
            store.put_candidate_constraint_assessment(assessment)
            assessments.append(assessment)

        assert tuple(store.iter_candidate_constraint_assessments(candidate.id)) == tuple(
            assessments
        )
        assert tuple(store.iter_candidate_constraint_assessments("missing")) == ()
