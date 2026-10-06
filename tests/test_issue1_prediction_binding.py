"""Regression test for prediction-to-hypothesis binding in positional evaluation."""

from collections import Counter

from test_autonomy import AdaptiveFixturePlanner, CREATED, _held_out_record, _records
from episteme.autonomy import run_autonomous_discovery
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
