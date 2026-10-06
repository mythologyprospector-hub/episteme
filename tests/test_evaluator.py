from episteme.autonomy import record_prediction_consequences
from episteme.evaluator import PositionalPredictionEvaluator
from episteme.executor import PositionalObservationExecutor
from dataclasses import replace

from episteme.model import (
    DiscoveryExpectation,
    DiscoveryExpectationKind,
    DiscoveryFinding,
    DiscoveryFindingKind,
    PredictionEvaluationOutcome,
    Provenance,
    Record,
    RecordKind,
)
from episteme.proposals import predict, propose_experiment, propose_hypothesis
from episteme.store import Store

CREATED = "2026-10-05T00:00:00Z"
PROVENANCE = (Provenance(source_id="evaluator-fixture", captured_at=CREATED,
                          source_location="https://example.org/evaluator",
                          source_version="1"),)


def _record(index: int, position: float) -> Record:
    return Record(id=f"bbbbbbbb-{index:04d}-4aaa-8aaa-bbbbbbbbbbbb",
                  kind=RecordKind.OBSERVATION, payload={"position": position},
                  provenance=PROVENANCE, created_at=CREATED)


def _setup():
    store = Store()
    records = (_record(1, 1.0), _record(2, 2.0), _record(3, 4.0))
    for record in records:
        store.put_record(record)

    finding = DiscoveryFinding(
        id="cccccccc-0001-4aaa-8aaa-cccccccccccc",
        kind=DiscoveryFindingKind.GAP,
        title="fixture gap", description="fixture gap",
        input_ids=tuple(record.id for record in records),
        method="fixture", method_version="1", rationale="fixture", measures=(),
        created_at=CREATED,
        expectation=DiscoveryExpectation(
            kind=DiscoveryExpectationKind.POSITIONAL, data={"position": 3.0}),
    )
    store.put_discovery_finding(finding)

    hypotheses = []
    for statement in ("position 3.0 is occupied", "position 3.0 is absent"):
        hypothesis = propose_hypothesis(
            statement=statement, finding_ids=(finding.id,),
            input_ids=tuple(record.id for record in records),
            method="fixture", method_version="1", rationale="fixture",
            created_at=CREATED)
        store.put_hypothesis(hypothesis)
        hypotheses.append(hypothesis)

    predictions = []
    for hypothesis in hypotheses:
        prediction = predict(
            source_id=hypothesis.id, consequence=hypothesis.statement,
            conditions="same observations", method="fixture", method_version="1",
            rationale="fixture",
            comparison_hypothesis_ids=tuple(item.id for item in hypotheses),
            expected_presence=(hypothesis.statement == "position 3.0 is occupied"),
            created_at=CREATED)
        store.put_prediction(prediction)
        predictions.append(prediction)

    proposal = propose_experiment(
        prediction_ids=tuple(item.id for item in predictions),
        objective="measure whether position 3.0 is occupied",
        proposed_observation="the observed positions",
        discrimination_basis="presence or absence of 3.0 discriminates the hypotheses",
        conditions="same observations", method="positional_observation",
        method_version="1", rationale="fixture", created_at=CREATED)
    store.put_experiment_proposal(proposal)

    result = PositionalObservationExecutor().execute(
        store, proposal, input_ids=tuple(record.id for record in records),
        created_at=CREATED)
    return store, proposal, tuple(predictions), result


def test_positional_evaluator_records_consistent_and_inconsistent_results():
    store, proposal, predictions, result = _setup()
    try:
        evaluations = PositionalPredictionEvaluator(position=3.0).evaluate(store, result, proposal, predictions,
                   comparison_conditions="same observations", created_at=CREATED)

        assert [item.outcome for item in evaluations] == [
            PredictionEvaluationOutcome.INCONSISTENT,
            PredictionEvaluationOutcome.CONSISTENT,
        ]
        assert all(store.get_prediction_evaluation(item.id) == item for item in evaluations)
        assert all(item.result_id == result.id for item in evaluations)
        assert all(item.experiment_proposal_id == proposal.id for item in evaluations)
    finally:
        store.close()


def test_positional_evaluator_refuses_missing_executable_expectation():
    store, proposal, predictions, result = _setup()
    predictions = tuple(
        replace(prediction, expected_presence=(True if index == 0 else None))
        for index, prediction in enumerate(predictions)
    )
    try:
        try:
            PositionalPredictionEvaluator(position=3.0).evaluate(
                store, result, proposal, predictions,
                comparison_conditions="same observations", created_at=CREATED)
        except ValueError as exc:
            assert "missing executable expectation" in str(exc)
        else:
            raise AssertionError("expected missing executable expectation to fail")
    finally:
        store.close()


def test_prediction_evaluations_become_explicit_knowledge_consequences():
    store, proposal, predictions, result = _setup()
    try:
        predictions = tuple(
            replace(prediction, expected_presence=(index == 0))
            for index, prediction in enumerate(predictions)
        )
        evaluations = PositionalPredictionEvaluator(position=3.0).evaluate(
            store, result, proposal, predictions,
            comparison_conditions="same observations", created_at=CREATED)

        consequence_ids = record_prediction_consequences(
            store, evaluations, created_at=CREATED
        )

        assert len(consequence_ids) == 2
        consequences = tuple(
            store.get_knowledge_state_consequence(item_id)
            for item_id in consequence_ids
        )
        assert all(item is not None for item in consequences)
        assert {item.consequence.value for item in consequences if item is not None} == {
            "supports", "contradicts"
        }
    finally:
        store.close()


def test_positional_evaluator_uses_numeric_tolerance_for_measurements():
    store, proposal, predictions, result = _setup()
    tolerant_result = replace(
        result,
        id="dddddddd-0001-4aaa-8aaa-dddddddddddd",
        payload={**result.payload, "observed_positions": [1.0, 2.0, 3.0000000005, 4.0]},
    )
    store.put_record(tolerant_result)
    try:
        evaluations = PositionalPredictionEvaluator(position=3.0).evaluate(
            store,
            tolerant_result,
            proposal,
            predictions,
            comparison_conditions="same observations",
            created_at=CREATED,
        )
        assert [item.outcome for item in evaluations] == [
            PredictionEvaluationOutcome.CONSISTENT,
            PredictionEvaluationOutcome.INCONSISTENT,
        ]
    finally:
        store.close()
