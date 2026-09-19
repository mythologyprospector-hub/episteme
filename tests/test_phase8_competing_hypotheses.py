"""Phase 8 proof that existing primitives can represent competing explanations."""

from episteme import (
    PredictionEvaluation,
    PredictionEvaluationOutcome,
    Provenance,
    Record,
    RecordKind,
    Store,
    DiscoveryFinding,
    DiscoveryFindingKind,
    DiscoveryMeasure,
    predict,
    propose_experiment,
    propose_hypothesis,
    discover_competing_prediction_opportunities,
)

CREATED = "2026-09-19T00:00:00Z"
PROVENANCE = (
    Provenance(
        source_id="phase8-competing-fixture",
        captured_at=CREATED,
        source_location="https://example.org/phase8",
        source_version="1",
    ),
)


def test_existing_primitives_can_discriminate_competing_hypotheses():
    finding = DiscoveryFinding(
        id="11111111-1111-4111-8111-111111111111",
        kind=DiscoveryFindingKind.TENSION,
        title="Competing explanations",
        description="One bounded observation admits two explicitly represented explanations.",
        input_ids=("22222222-2222-4222-8222-222222222222",),
        method="phase8-competing-fixture",
        method_version="1",
        rationale="The fixture proves competing-hypothesis representation without automatic inference.",
        measures=(
            DiscoveryMeasure(
                name="hypothesis_count",
                value=2.0,
                scale="count",
                basis="two explicit competing hypotheses",
            ),
        ),
        created_at=CREATED,
    )
    result = Record(
        id="22222222-2222-4222-8222-222222222222",
        kind=RecordKind.RESULT,
        payload={"observed": "outcome-a"},
        provenance=PROVENANCE,
        created_at=CREATED,
    )

    with Store() as store:
        store.put_record(result)
        store.put_discovery_finding(finding)

        hypothesis_a = propose_hypothesis(
            statement="Explanation A predicts outcome A.",
            finding_ids=(finding.id,),
            input_ids=(result.id,),
            method="phase8-competing-fixture",
            method_version="1",
            rationale="Explicit candidate explanation.",
            created_at="2026-09-19T00:00:01Z",
        )
        hypothesis_b = propose_hypothesis(
            statement="Explanation B predicts outcome B.",
            finding_ids=(finding.id,),
            input_ids=(result.id,),
            method="phase8-competing-fixture",
            method_version="1",
            rationale="Explicit competing candidate explanation.",
            created_at="2026-09-19T00:00:02Z",
        )
        store.put_hypothesis(hypothesis_a)
        store.put_hypothesis(hypothesis_b)

        prediction_a = predict(
            source_id=hypothesis_a.id,
            consequence="Outcome A will be observed.",
            conditions="Same bounded test conditions.",
            method="phase8-competing-fixture",
            method_version="1",
            rationale="Prediction derived from Explanation A.",
            comparison_hypothesis_ids=(hypothesis_a.id, hypothesis_b.id),
            created_at="2026-09-19T00:00:03Z",
        )
        prediction_b = predict(
            source_id=hypothesis_b.id,
            consequence="Outcome B will be observed.",
            conditions="Same bounded test conditions.",
            method="phase8-competing-fixture",
            method_version="1",
            rationale="Prediction derived from Explanation B.",
            comparison_hypothesis_ids=(hypothesis_a.id, hypothesis_b.id),
            created_at="2026-09-19T00:00:04Z",
        )
        store.put_prediction(prediction_a)
        store.put_prediction(prediction_b)

        findings = discover_competing_prediction_opportunities(
            store,
            created_at="2026-09-19T00:00:04Z",
        )
        assert len(findings) == 1
        opportunity = findings[0]
        assert opportunity.kind is DiscoveryFindingKind.TENSION
        assert opportunity.input_ids == (result.id,)
        assert set(opportunity.context_ids) == {prediction_a.id, prediction_b.id}
        assert "different predicted consequences" in opportunity.rationale
        store.put_discovery_finding(opportunity)

        proposal = propose_experiment(
            prediction_ids=(prediction_a.id, prediction_b.id),
            objective="Distinguish the two competing explanations.",
            proposed_observation="Measure which of outcome A or outcome B occurs under the shared conditions.",
            discrimination_basis="The same proposed observation has different predicted outcomes under the two hypotheses.",
            conditions="Same bounded test conditions.",
            method="phase8-competing-fixture",
            method_version="1",
            rationale="A single observation is used to discriminate explicitly represented predictions.",
            created_at="2026-09-19T00:00:05Z",
        )
        store.put_experiment_proposal(proposal)

        evaluation_a = PredictionEvaluation(
            id="33333333-3333-4333-8333-333333333333",
            result_id=result.id,
            prediction_id=prediction_a.id,
            experiment_proposal_id=proposal.id,
            comparison_conditions="Same bounded test conditions.",
            assumptions=(),
            outcome=PredictionEvaluationOutcome.CONSISTENT,
            rationale="The grounded result matches outcome A.",
            method="phase8-competing-fixture",
            method_version="1",
            created_at="2026-09-19T00:00:06Z",
        )
        evaluation_b = PredictionEvaluation(
            id="44444444-4444-4444-8444-444444444444",
            result_id=result.id,
            prediction_id=prediction_b.id,
            experiment_proposal_id=proposal.id,
            comparison_conditions="Same bounded test conditions.",
            assumptions=(),
            outcome=PredictionEvaluationOutcome.INCONSISTENT,
            rationale="The grounded result does not match outcome B.",
            method="phase8-competing-fixture",
            method_version="1",
            created_at="2026-09-19T00:00:07Z",
        )
        store.put_prediction_evaluation(evaluation_a)
        store.put_prediction_evaluation(evaluation_b)

        stored_proposal = store.get_experiment_proposal(proposal.id)
        stored_a = store.get_prediction(prediction_a.id)
        stored_b = store.get_prediction(prediction_b.id)

    assert stored_proposal is not None
    assert stored_proposal.prediction_ids == (prediction_a.id, prediction_b.id)
    assert stored_a is not None
    assert stored_b is not None
    assert stored_a.comparison_hypothesis_ids == (hypothesis_a.id, hypothesis_b.id)
    assert stored_b.comparison_hypothesis_ids == (hypothesis_a.id, hypothesis_b.id)
    assert evaluation_a.outcome is PredictionEvaluationOutcome.CONSISTENT
    assert evaluation_b.outcome is PredictionEvaluationOutcome.INCONSISTENT
