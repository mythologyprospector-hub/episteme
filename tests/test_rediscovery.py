import math
from dataclasses import replace

from episteme.discovery import detect_positional_gap
from episteme.autonomy import _validate_experiment_input_independence
from episteme.model import PredictionEvaluationOutcome
from episteme.proposals import predict, propose_experiment, complete_structural_gap
from episteme.discovery import detect_positional_gap
from episteme.rediscovery import (
    RediscoveryOutcome,
    FIXTURE_CAPTURED_AT,
    build_mendeleev_fixture,
    derive_mendeleev_mass_prediction,
    evaluate_mendeleev_mass_prediction,
)


def test_phase29_fixture_separates_pre_discovery_and_held_out_records():
    fixture = build_mendeleev_fixture()

    pre_ids = {record.id for record in fixture.pre_discovery_records}
    assert fixture.held_out_record.id not in pre_ids
    assert len(pre_ids) == len(fixture.pre_discovery_records)
    assert len(fixture.pre_discovery_records) >= 3


def test_phase29_pre_discovery_fixture_contains_the_structural_vacancy():
    fixture = build_mendeleev_fixture()

    periods = sorted(
        record.payload["period"] for record in fixture.pre_discovery_records
        if record.payload["family"] == "group_14"
    )
    assert periods == [2, 3, 5, 6]
    assert fixture.held_out_record.payload["period"] == 4


def test_phase29_planner_fixture_does_not_expose_later_element_identity_or_modern_atomic_number():
    fixture = build_mendeleev_fixture()

    public_payload = [
        record.to_dict()["payload"] for record in fixture.pre_discovery_records
    ]
    public_text = str(public_payload).lower()

    assert "germanium" not in public_text
    assert "72.32" not in public_text
    assert "5.47" not in public_text
    assert "atomic_number" not in public_text
    assert fixture.held_out_record.payload["label"] == "held_out_element"


def test_phase29_held_out_record_is_not_in_pre_discovery_inputs():
    fixture = build_mendeleev_fixture()

    pre_ids = tuple(record.id for record in fixture.pre_discovery_records)
    assert fixture.held_out_record.id not in pre_ids
    assert fixture.held_out_record.created_at > max(
        record.created_at for record in fixture.pre_discovery_records
    )


def test_phase29_host_runtime_derives_nontrivial_mass_prediction_from_pre_discovery_inputs():
    fixture = build_mendeleev_fixture()

    prediction = derive_mendeleev_mass_prediction(fixture.pre_discovery_records)

    assert math.isclose(prediction.predicted_relative_atomic_mass, 73.4)
    assert prediction.input_ids == (
        fixture.pre_discovery_records[1].id,
        fixture.pre_discovery_records[2].id,
    )
    assert prediction.input_ids[0] != fixture.held_out_record.id
    assert prediction.input_ids[1] != fixture.held_out_record.id


def test_phase29_deterministic_evaluator_matches_later_held_out_observation():
    fixture = build_mendeleev_fixture()
    prediction = derive_mendeleev_mass_prediction(fixture.pre_discovery_records)

    evaluation = evaluate_mendeleev_mass_prediction(
        prediction,
        fixture.held_out_record,
        tolerance=0.05,
    )

    assert evaluation.outcome is RediscoveryOutcome.MATCHED
    assert evaluation.observed_relative_atomic_mass == 72.63
    assert evaluation.relative_error < 0.02


def test_phase29_corrupted_held_out_evidence_fails_deterministically():
    fixture = build_mendeleev_fixture()
    prediction = derive_mendeleev_mass_prediction(fixture.pre_discovery_records)
    corrupted_payload = dict(fixture.held_out_record.payload)
    corrupted_payload["relative_atomic_mass"] = 200.0
    corrupted = replace(fixture.held_out_record, payload=corrupted_payload)

    evaluation = evaluate_mendeleev_mass_prediction(
        prediction,
        corrupted,
        tolerance=0.05,
    )

    assert evaluation.outcome is RediscoveryOutcome.FAILED
    assert evaluation.relative_error > 0.5


def test_phase29_runtime_executes_and_evaluates_through_host_experiment_boundary():
    from episteme.rediscovery import RediscoveryExperimentExecutor, RediscoveryPredictionEvaluator
    from episteme.store import Store

    fixture = build_mendeleev_fixture()
    prediction_value = derive_mendeleev_mass_prediction(
        fixture.pre_discovery_records
    ).predicted_relative_atomic_mass

    with Store() as store:
        for record in fixture.pre_discovery_records + (fixture.held_out_record,):
            store.put_record(record)

        finding = detect_positional_gap(
            store,
            tuple(record.id for record in fixture.pre_discovery_records),
            "period",
            1.0,
            FIXTURE_CAPTURED_AT,
        )
        assert finding is not None
        store.put_discovery_finding(finding)

        hypothesis = complete_structural_gap(
            store,
            gap_id=finding.id,
            statement="the missing period-4 element has a predictable relative atomic mass",
            method="phase29-fixture",
            method_version="1",
            rationale="fixture hypothesis",
            created_at=FIXTURE_CAPTURED_AT,
        )
        store.put_hypothesis(hypothesis)

        prediction = predict(
            source_id=hypothesis.id,
            consequence="the missing period-4 mass is approximately the forecast value",
            conditions="group-14 period-4 gap",
            method="phase29-fixture",
            method_version="1",
            rationale="machine-checkable rediscovery forecast",
            predicted_numeric_value=prediction_value,
            created_at=FIXTURE_CAPTURED_AT,
        )
        store.put_prediction(prediction)

        proposal = propose_experiment(
            prediction_ids=(prediction.id,),
            objective="test the quantitative rediscovery forecast",
            proposed_observation="the held-out period-4 relative atomic mass",
            discrimination_basis="pre-registered quantitative comparison",
            conditions="historical fixture conditions",
            method="phase29-fixture",
            method_version="1",
            rationale="bounded held-out evaluation",
            created_at=FIXTURE_CAPTURED_AT,
        )
        store.put_experiment_proposal(proposal)

        result = RediscoveryExperimentExecutor().execute(
            store,
            proposal,
            input_ids=(fixture.held_out_record.id,),
            created_at="1886-12-31T00:00:00+00:00",
        )
        evaluations = RediscoveryPredictionEvaluator(
            pre_discovery_records=fixture.pre_discovery_records,
            tolerance=0.05,
        ).evaluate(
            store,
            result,
            proposal,
            (prediction,),
            comparison_conditions="relative atomic mass",
            created_at="1886-12-31T00:00:00+00:00",
        )

        assert result.payload["input_ids"] == [fixture.held_out_record.id]
        assert result.payload["observed_relative_atomic_mass"] == 72.63
        assert evaluations[0].outcome is PredictionEvaluationOutcome.CONSISTENT
        assert "73.4" in evaluations[0].rationale
        assert "72.32" in evaluations[0].rationale


def test_phase29_experiment_rejects_identity_distinct_clone_of_discovery_record():
    from dataclasses import replace
    from episteme.store import Store

    fixture = build_mendeleev_fixture()
    original = fixture.pre_discovery_records[1]
    clone = replace(
        original,
        id="30000000-0000-4000-8000-000000000001",
    )

    with Store() as store:
        store.put_record(original)
        store.put_record(clone)

        try:
            _validate_experiment_input_independence(
                store,
                (original.id,),
                (clone.id,),
            )
        except RuntimeError as exc:
            assert "content/provenance duplicate" in str(exc)
        else:
            raise AssertionError(
                "identity-distinct clone must not qualify as independent held-out evidence"
            )


def test_phase29_baseline_reports_property_specific_errors():
    from episteme.rediscovery import REDISCOVERY_CASES, derive_adjacent_midpoint

    fixture = build_mendeleev_fixture()
    expected = {
        "relative_atomic_mass": 73.3975,
        "density_g_cm3": 4.8083,
        "melting_point_c": 822.964,
    }
    for case in REDISCOVERY_CASES:
        baseline = derive_adjacent_midpoint(
            fixture.pre_discovery_records,
            property_key=case.property_key,
        )
        assert math.isclose(baseline, expected[case.property_key])


def test_phase29_numeric_predictions_must_be_distinct():
    import pytest
    from episteme.autonomy import DiscoveryAction, PlannerActionError

    with pytest.raises(PlannerActionError, match="distinct predicted values"):
        DiscoveryAction(
            kind="prediction",
            target_ids=("one", "two"),
            conditions="bounded",
            consequence="numeric forecast",
            predicted_numeric_values={"one": 73.4, "two": 73.4},
            rationale="distinctness test",
        )
