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
    propose_discriminating_prediction,
    propose_candidate_discrimination_experiment,
    PredictionEvaluation,
    PredictionEvaluationOutcome,
    KnowledgeStateConsequence,
    KnowledgeStateConsequenceKind,
    KnowledgeStateTargetKind,
    detect_positional_gap,
    discover_evaluation_tensions,
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


def test_candidate_discriminating_prediction_preserves_competing_candidates():
    records = _fixture()

    with Store() as store:
        for record in records:
            store.put_record(record)
        gap = detect_positional_gap(
            store,
            record_ids=tuple(record.id for record in records),
            position_key="position",
            step=1.0,
            created_at="2026-09-19T00:10:00Z",
        )
        assert gap is not None
        store.put_discovery_finding(gap)

        candidate_a = complete_structural_gap(
            store,
            gap_id=gap.id,
            statement="The missing occupant is candidate A.",
            method="phase10-fixture",
            method_version="1",
            rationale="Explicit candidate completion.",
            created_at="2026-09-19T00:10:01Z",
        )
        candidate_b = complete_structural_gap(
            store,
            gap_id=gap.id,
            statement="The missing occupant is candidate B.",
            method="phase10-fixture",
            method_version="1",
            rationale="Explicit competing candidate completion.",
            created_at="2026-09-19T00:10:02Z",
        )
        store.put_hypothesis(candidate_a)
        store.put_hypothesis(candidate_b)

        prediction = propose_discriminating_prediction(
            store,
            candidate_id=candidate_a.id,
            competing_candidate_ids=(candidate_a.id, candidate_b.id),
            consequence="The missing position will exhibit outcome A.",
            conditions="The same bounded structural conditions apply.",
            method="phase10-fixture",
            method_version="1",
            rationale="The consequence distinguishes the two explicit candidates.",
            created_at="2026-09-19T00:10:03Z",
        )
        store.put_prediction(prediction)

        assert prediction.source_id == candidate_a.id
        assert prediction.comparison_hypothesis_ids == (candidate_a.id, candidate_b.id)
        assert store.get_hypothesis(candidate_a.id) == candidate_a
        assert store.get_hypothesis(candidate_b.id) == candidate_b
        assert store.get_discovery_finding(gap.id) == gap


def test_candidate_discriminating_prediction_rejects_missing_competitor():
    records = _fixture()

    with Store() as store:
        for record in records:
            store.put_record(record)
        gap = detect_positional_gap(
            store,
            record_ids=tuple(record.id for record in records),
            position_key="position",
            step=1.0,
            created_at="2026-09-19T00:11:00Z",
        )
        assert gap is not None
        store.put_discovery_finding(gap)

        candidate = complete_structural_gap(
            store,
            gap_id=gap.id,
            statement="The missing occupant is candidate A.",
            method="phase10-fixture",
            method_version="1",
            rationale="Explicit candidate completion.",
            created_at="2026-09-19T00:11:01Z",
        )
        store.put_hypothesis(candidate)

        with pytest.raises(ValueError, match="references missing candidate"):
            propose_discriminating_prediction(
                store,
                candidate_id=candidate.id,
                competing_candidate_ids=(
                    candidate.id,
                    "aaaaaaaa-0000-4000-8000-aaaaaaaaaaaa",
                ),
                consequence="The missing position will exhibit outcome A.",
                conditions="The same bounded structural conditions apply.",
                method="phase10-fixture",
                method_version="1",
                rationale="Missing competitor must remain explicit.",
                created_at="2026-09-19T00:11:02Z",
            )


def test_candidate_discrimination_enters_existing_experiment_proposal_without_mutation():
    records = _fixture()

    with Store() as store:
        for record in records:
            store.put_record(record)
        gap = detect_positional_gap(
            store,
            record_ids=tuple(record.id for record in records),
            position_key="position",
            step=1.0,
            created_at="2026-09-19T00:20:00Z",
        )
        assert gap is not None
        store.put_discovery_finding(gap)

        candidate_a = complete_structural_gap(
            store,
            gap_id=gap.id,
            statement="The missing occupant is candidate A.",
            method="phase10-fixture",
            method_version="1",
            rationale="Explicit candidate completion.",
            created_at="2026-09-19T00:20:01Z",
        )
        candidate_b = complete_structural_gap(
            store,
            gap_id=gap.id,
            statement="The missing occupant is candidate B.",
            method="phase10-fixture",
            method_version="1",
            rationale="Explicit competing candidate completion.",
            created_at="2026-09-19T00:20:02Z",
        )
        store.put_hypothesis(candidate_a)
        store.put_hypothesis(candidate_b)

        prediction_a = propose_discriminating_prediction(
            store,
            candidate_id=candidate_a.id,
            competing_candidate_ids=(candidate_a.id, candidate_b.id),
            consequence="Outcome A occurs.",
            conditions="Shared bounded test conditions.",
            method="phase10-fixture",
            method_version="1",
            rationale="Candidate A predicts a distinct outcome.",
            created_at="2026-09-19T00:20:03Z",
        )
        prediction_b = propose_discriminating_prediction(
            store,
            candidate_id=candidate_b.id,
            competing_candidate_ids=(candidate_a.id, candidate_b.id),
            consequence="Outcome B occurs.",
            conditions="Shared bounded test conditions.",
            method="phase10-fixture",
            method_version="1",
            rationale="Candidate B predicts a distinct outcome.",
            created_at="2026-09-19T00:20:04Z",
        )
        store.put_prediction(prediction_a)
        store.put_prediction(prediction_b)

        gap_before = gap.to_dict()
        candidate_a_before = candidate_a.to_dict()
        candidate_b_before = candidate_b.to_dict()
        grounded_before = [store.get_record(record.id) for record in records]

        proposal = propose_candidate_discrimination_experiment(
            store,
            prediction_ids=(prediction_a.id, prediction_b.id),
            objective="Distinguish candidate A from candidate B.",
            proposed_observation="Observe whether outcome A or outcome B occurs.",
            discrimination_basis="The candidates predict different outcomes under shared conditions.",
            conditions="Shared bounded test conditions.",
            method="phase10-fixture",
            method_version="1",
            rationale="The existing experiment proposal primitive can carry the candidate-derived predictions.",
            created_at="2026-09-19T00:20:05Z",
        )
        store.put_experiment_proposal(proposal)

        assert proposal.prediction_ids == (prediction_a.id, prediction_b.id)
        assert proposal.discrimination_basis == "The candidates predict different outcomes under shared conditions."
        assert store.get_discovery_finding(gap.id).to_dict() == gap_before
        assert store.get_hypothesis(candidate_a.id).to_dict() == candidate_a_before
        assert store.get_hypothesis(candidate_b.id).to_dict() == candidate_b_before
        assert [store.get_record(record.id) for record in records] == grounded_before
        assert store.get_experiment_proposal(proposal.id) == proposal


def test_candidate_discrimination_experiment_rejects_non_discriminating_prediction():
    records = _fixture()

    with Store() as store:
        for record in records:
            store.put_record(record)
        gap = detect_positional_gap(
            store,
            record_ids=tuple(record.id for record in records),
            position_key="position",
            step=1.0,
            created_at="2026-09-19T00:21:00Z",
        )
        assert gap is not None
        store.put_discovery_finding(gap)

        candidate = complete_structural_gap(
            store,
            gap_id=gap.id,
            statement="The missing occupant is candidate A.",
            method="phase10-fixture",
            method_version="1",
            rationale="Explicit candidate completion.",
            created_at="2026-09-19T00:21:01Z",
        )
        store.put_hypothesis(candidate)

        # Build a valid single-candidate prediction directly to prove the
        # experiment boundary does not silently accept it.
        from episteme import predict
        prediction = predict(
            source_id=candidate.id,
            consequence="Outcome A occurs.",
            conditions="Shared bounded test conditions.",
            method="phase10-fixture",
            method_version="1",
            rationale="Single-candidate prediction.",
            created_at="2026-09-19T00:21:03Z",
        )
        store.put_prediction(prediction)

        with pytest.raises(ValueError, match="requires at least two predictions"):
            propose_candidate_discrimination_experiment(
                store,
                prediction_ids=(prediction.id,),
                objective="Invalid discrimination.",
                proposed_observation="Observe the outcome.",
                discrimination_basis="No competing prediction exists.",
                conditions="Shared bounded test conditions.",
                method="phase10-fixture",
                method_version="1",
                rationale="Boundary proof.",
                created_at="2026-09-19T00:21:04Z",
            )


def test_candidate_discrimination_closes_through_result_evaluation_and_consequence():
    records = _fixture()

    with Store() as store:
        for record in records:
            store.put_record(record)

        gap = detect_positional_gap(
            store,
            record_ids=tuple(record.id for record in records),
            position_key="position",
            step=1.0,
            created_at="2026-09-19T00:30:00Z",
        )
        assert gap is not None
        store.put_discovery_finding(gap)

        candidate_a = complete_structural_gap(
            store,
            gap_id=gap.id,
            statement="The missing occupant has position 3.0.",
            method="phase10-loop-fixture",
            method_version="1",
            rationale="Candidate A fills the established positional gap.",
            created_at="2026-09-19T00:30:01Z",
        )
        candidate_b = complete_structural_gap(
            store,
            gap_id=gap.id,
            statement="The missing occupant has a different position.",
            method="phase10-loop-fixture",
            method_version="1",
            rationale="Candidate B provides a competing completion.",
            created_at="2026-09-19T00:30:02Z",
        )
        store.put_hypothesis(candidate_a)
        store.put_hypothesis(candidate_b)

        prediction_a = propose_discriminating_prediction(
            store,
            candidate_id=candidate_a.id,
            competing_candidate_ids=(candidate_a.id, candidate_b.id),
            consequence="The measured occupant is at position 3.0.",
            conditions="Same bounded test conditions.",
            method="phase10-loop-fixture",
            method_version="1",
            rationale="Candidate A predicts the missing position directly.",
            created_at="2026-09-19T00:30:03Z",
        )
        prediction_b = propose_discriminating_prediction(
            store,
            candidate_id=candidate_b.id,
            competing_candidate_ids=(candidate_a.id, candidate_b.id),
            consequence="The measured occupant is not at position 3.0.",
            conditions="Same bounded test conditions.",
            method="phase10-loop-fixture",
            method_version="1",
            rationale="Candidate B predicts a different outcome.",
            created_at="2026-09-19T00:30:04Z",
        )
        store.put_prediction(prediction_a)
        store.put_prediction(prediction_b)

        proposal = propose_candidate_discrimination_experiment(
            store,
            prediction_ids=(prediction_a.id, prediction_b.id),
            objective="Determine which candidate matches the observed occupant.",
            proposed_observation="Measure the missing position.",
            discrimination_basis="The candidates predict different positions under the same conditions.",
            conditions="Same bounded test conditions.",
            method="phase10-loop-fixture",
            method_version="1",
            rationale="The proposed measurement directly distinguishes the competing predictions.",
            created_at="2026-09-19T00:30:05Z",
        )
        store.put_experiment_proposal(proposal)

        result = Record(
            id="55555555-5555-4555-8555-555555555555",
            kind=RecordKind.RESULT,
            payload={"position": 3.0},
            provenance=PROVENANCE,
            created_at="2026-09-19T00:30:06Z",
        )
        store.put_record(result)

        evaluation_a = PredictionEvaluation(
            id="66666666-6666-4666-8666-666666666666",
            result_id=result.id,
            prediction_id=prediction_a.id,
            experiment_proposal_id=proposal.id,
            comparison_conditions="Same bounded test conditions.",
            assumptions=(),
            outcome=PredictionEvaluationOutcome.CONSISTENT,
            rationale="The grounded result matches candidate A's predicted position.",
            method="phase10-loop-fixture",
            method_version="1",
            created_at="2026-09-19T00:30:07Z",
        )
        evaluation_b = PredictionEvaluation(
            id="77777777-7777-4777-8777-777777777777",
            result_id=result.id,
            prediction_id=prediction_b.id,
            experiment_proposal_id=proposal.id,
            comparison_conditions="Same bounded test conditions.",
            assumptions=(),
            outcome=PredictionEvaluationOutcome.INCONSISTENT,
            rationale="The grounded result does not match candidate B's predicted position.",
            method="phase10-loop-fixture",
            method_version="1",
            created_at="2026-09-19T00:30:08Z",
        )
        store.put_prediction_evaluation(evaluation_a)
        store.put_prediction_evaluation(evaluation_b)

        consequence_a = KnowledgeStateConsequence(
            id="88888888-8888-4888-8888-888888888888",
            evaluation_ids=(evaluation_a.id,),
            target_kind=KnowledgeStateTargetKind.HYPOTHESIS,
            target_id=candidate_a.id,
            consequence=KnowledgeStateConsequenceKind.SUPPORTS,
            assumptions=(),
            rationale="The grounded result is consistent with candidate A.",
            method="phase10-loop-fixture",
            method_version="1",
            created_at="2026-09-19T00:30:09Z",
        )
        consequence_b = KnowledgeStateConsequence(
            id="99999999-9999-4999-8999-999999999999",
            evaluation_ids=(evaluation_b.id,),
            target_kind=KnowledgeStateTargetKind.HYPOTHESIS,
            target_id=candidate_b.id,
            consequence=KnowledgeStateConsequenceKind.WEAKENS,
            assumptions=(),
            rationale="The grounded result is inconsistent with candidate B.",
            method="phase10-loop-fixture",
            method_version="1",
            created_at="2026-09-19T00:30:10Z",
        )
        store.put_knowledge_state_consequence(consequence_a)
        store.put_knowledge_state_consequence(consequence_b)

        assert result.kind is RecordKind.RESULT
        assert store.get_record(result.id) == result
        assert store.get_prediction_evaluation(evaluation_a.id) == evaluation_a
        assert store.get_prediction_evaluation(evaluation_b.id) == evaluation_b
        assert store.get_knowledge_state_consequence(consequence_a.id) == consequence_a
        assert store.get_knowledge_state_consequence(consequence_b.id) == consequence_b

        assert store.get_discovery_finding(gap.id) == gap
        assert store.get_hypothesis(candidate_a.id) == candidate_a
        assert store.get_hypothesis(candidate_b.id) == candidate_b
        assert store.get_prediction(prediction_a.id) == prediction_a
        assert store.get_prediction(prediction_b.id) == prediction_b
        assert store.get_experiment_proposal(proposal.id) == proposal


def test_closed_loop_can_renew_discovery_from_evaluation_tension():
    records = _fixture()

    with Store() as store:
        for record in records:
            store.put_record(record)

        gap = detect_positional_gap(
            store,
            record_ids=tuple(record.id for record in records),
            position_key="position",
            step=1.0,
            created_at="2026-09-19T00:40:00Z",
        )
        assert gap is not None
        store.put_discovery_finding(gap)

        candidate = complete_structural_gap(
            store,
            gap_id=gap.id,
            statement="The missing occupant has position 3.0.",
            method="phase10-renewal-fixture",
            method_version="1",
            rationale="Candidate fills the established gap.",
            created_at="2026-09-19T00:40:01Z",
        )
        store.put_hypothesis(candidate)

        prediction = propose_discriminating_prediction(
            store,
            candidate_id=candidate.id,
            competing_candidate_ids=(candidate.id, candidate.id),
            consequence="The measured occupant is at position 3.0.",
            conditions="Same bounded test conditions.",
            method="phase10-renewal-fixture",
            method_version="1",
            rationale="Fixture prediction for renewed discovery.",
            created_at="2026-09-19T00:40:02Z",
        )
        store.put_prediction(prediction)

        result_consistent = Record(
            id="aaaaaaa1-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            kind=RecordKind.RESULT,
            payload={"position": 3.0},
            provenance=PROVENANCE,
            created_at="2026-09-19T00:40:03Z",
        )
        result_inconsistent = Record(
            id="aaaaaaa2-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            kind=RecordKind.RESULT,
            payload={"position": 5.0},
            provenance=PROVENANCE,
            created_at="2026-09-19T00:40:04Z",
        )
        store.put_record(result_consistent)
        store.put_record(result_inconsistent)

        evaluation_consistent = PredictionEvaluation(
            id="bbbbbbb1-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
            result_id=result_consistent.id,
            prediction_id=prediction.id,
            comparison_conditions="Same bounded test conditions.",
            assumptions=(),
            outcome=PredictionEvaluationOutcome.CONSISTENT,
            rationale="One grounded result matches the prediction.",
            method="phase10-renewal-fixture",
            method_version="1",
            created_at="2026-09-19T00:40:05Z",
        )
        evaluation_inconsistent = PredictionEvaluation(
            id="bbbbbbb2-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
            result_id=result_inconsistent.id,
            prediction_id=prediction.id,
            comparison_conditions="Same bounded test conditions.",
            assumptions=(),
            outcome=PredictionEvaluationOutcome.INCONSISTENT,
            rationale="A second grounded result differs from the prediction.",
            method="phase10-renewal-fixture",
            method_version="1",
            created_at="2026-09-19T00:40:06Z",
        )
        store.put_prediction_evaluation(evaluation_consistent)
        store.put_prediction_evaluation(evaluation_inconsistent)

        renewed = discover_evaluation_tensions(
            store,
            created_at="2026-09-19T00:40:07Z",
        )

        assert len(renewed) == 1
        finding = renewed[0]
        assert finding.kind is DiscoveryFindingKind.TENSION
        assert finding.input_ids == (result_consistent.id, result_inconsistent.id)
        assert finding.context_ids == (
            evaluation_consistent.id,
            evaluation_inconsistent.id,
        )
        assert prediction.id in finding.description
        store.put_discovery_finding(finding)

        persisted = store.get_discovery_finding(finding.id)
        assert persisted == finding

        # The renewed finding is generated context around grounded results;
        # it does not rewrite the original gap, candidate, prediction, or results.
        assert store.get_discovery_finding(gap.id) == gap
        assert store.get_hypothesis(candidate.id) == candidate
        assert store.get_prediction(prediction.id) == prediction
        assert store.get_record(result_consistent.id) == result_consistent
        assert store.get_record(result_inconsistent.id) == result_inconsistent
