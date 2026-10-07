"""Regression test for prediction-to-hypothesis binding in positional evaluation."""

from collections import Counter

from test_autonomy import AdaptiveFixturePlanner, CREATED, _held_out_record, _records
from episteme.autonomy import DiscoveryAction, run_autonomous_discovery
from episteme.discovery import detect_positional_gap
from episteme.store import Store


def test_positional_verdicts_follow_prediction_hypothesis_not_prediction_order():
    """The supported hypothesis must be stable even when prediction order varies."""

    tally = Counter()
    for _ in range(30):
        records = _records()
        held_out = _held_out_record()
        with Store() as store:
            for record in (*records, held_out):
                store.put_record(record)

            gap = detect_positional_gap(
                store,
                record_ids=tuple(record.id for record in records),
                position_key="position",
                step=1.0,
                created_at=CREATED,
            )
            assert gap is not None
            store.put_discovery_finding(gap)

            result = run_autonomous_discovery(
                store,
                AdaptiveFixturePlanner(),
                grounded_input_ids=tuple(record.id for record in records),
                experiment_input_ids=(held_out.id,),
                started_at=CREATED,
            )
            assert result.status == "stopped", result.stop_reason

            hypotheses = {
                hypothesis.id: hypothesis.statement
                for hypothesis in store.iter_hypotheses()
            }
            prediction_to_hypothesis = {
                prediction.id: prediction.source_id
                for prediction in store.iter_predictions()
            }
            prediction_expectations = {
                prediction.id: prediction.expected_presence
                for prediction in store.iter_predictions()
            }
            assert set(prediction_expectations.values()) == {True, False}

            for evaluation in store.iter_prediction_evaluations():
                if evaluation.outcome.value == "consistent":
                    tally[
                        hypotheses[prediction_to_hypothesis[evaluation.prediction_id]]
                    ] += 1

    assert tally == Counter(
        {"The missing occupant is at position 3.0.": 30}
    )



def test_positional_experiment_rejects_prediction_expectation_contradicting_hypothesis():
    records = _records()
    held_out = _held_out_record()
    with Store() as store:
        for record in (*records, held_out):
            store.put_record(record)
        gap = detect_positional_gap(
            store,
            record_ids=tuple(record.id for record in records),
            position_key="position",
            step=1.0,
            created_at=CREATED,
        )
        assert gap is not None
        store.put_discovery_finding(gap)
        from episteme.proposals import propose_hypothesis, predict, propose_experiment
        from episteme.autonomy import PlannerActionError, execute_action

        supported = propose_hypothesis(
            statement="The missing occupant is at position 3.0.",
            finding_ids=(gap.id,), input_ids=tuple(r.id for r in records),
            method="fixture", method_version="1", rationale="fixture", created_at=CREATED,
        )
        competing = propose_hypothesis(
            statement="The missing occupant is not at position 3.0.",
            finding_ids=(gap.id,), input_ids=tuple(r.id for r in records),
            method="fixture", method_version="1", rationale="fixture", created_at=CREATED,
        )
        store.put_hypothesis(supported)
        store.put_hypothesis(competing)
        p1 = predict(source_id=supported.id, consequence="present", conditions="bounded", method="fixture", method_version="1", rationale="fixture", expected_presence=False, created_at=CREATED)
        p2 = predict(source_id=competing.id, consequence="absent", conditions="bounded", method="fixture", method_version="1", rationale="fixture", expected_presence=True, created_at=CREATED)
        store.put_prediction(p1)
        store.put_prediction(p2)
        action = DiscoveryAction(
            kind="experiment", target_ids=(p1.id, p2.id), objective="test", proposed_observation="measure", discrimination_basis="contrasting predictions", conditions="bounded", rationale="fixture",
            execution_spec={"operation": "positional_presence", "position": 3.0},
        )
        try:
            execute_action(store, action, created_at=CREATED)
        except PlannerActionError as exc:
            assert "contradicts its source hypothesis" in str(exc)
        else:
            raise AssertionError("contradictory positional prediction binding was accepted")
