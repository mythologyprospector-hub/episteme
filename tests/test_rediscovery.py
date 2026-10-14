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

    assert math.isclose(prediction.predicted_relative_atomic_mass, 73.3975)
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
            quantitative_rule={"operation": "midpoint", "inputs": [1.0, 3.0]},
            created_at=FIXTURE_CAPTURED_AT,
        )
        store.put_hypothesis(hypothesis)
        expected_rule = {"operation": "midpoint", "inputs": [1.0, 3.0]}
        assert store.get_hypothesis(hypothesis.id).quantitative_rule == expected_rule
        assert next(item for item in store.iter_hypotheses() if item.id == hypothesis.id).quantitative_rule == expected_rule

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
        assert "73.3975" in evaluations[0].rationale
        assert "72.63" in evaluations[0].rationale
        assert "baseline_error" in evaluations[0].rationale
        assert "model_error" in evaluations[0].rationale
        assert "verdict=ties_baseline" in evaluations[0].rationale


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


def test_phase29_duplicate_competing_hypothesis_is_rejected():
    import pytest
    from episteme.autonomy import DiscoveryAction, PlannerActionError, execute_action
    from episteme.store import Store

    fixture = build_mendeleev_fixture()
    with Store() as store:
        for record in fixture.pre_discovery_records:
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
        first = complete_structural_gap(
            store,
            gap_id=finding.id,
            statement="the candidate follows a regular group trend",
            method="test",
            method_version="1",
            rationale="first candidate",
            created_at=FIXTURE_CAPTURED_AT,
        )
        store.put_hypothesis(first)

        with pytest.raises(PlannerActionError, match="duplicate hypothesis statement"):
            execute_action(
                store,
                DiscoveryAction(
                    kind="hypothesis",
                    target_ids=(finding.id,),
                    statement="the candidate follows a regular group trend",
                    rationale="duplicate candidate",
                ),
                created_at=FIXTURE_CAPTURED_AT,
            )


def test_rediscovery_diagnostic_independently_computes_supported_quantitative_rules():
    from scripts.accept_ollama_rediscovery import _rule_derived_value
    from episteme.rediscovery import build_mendeleev_fixture

    fixture = build_mendeleev_fixture()
    records = fixture.pre_discovery_records

    midpoint, detail = _rule_derived_value(
        {"operation": "midpoint", "input_positions": [3, 5]},
        records,
        "relative_atomic_mass",
    )
    assert math.isclose(midpoint, 73.3975)
    assert detail == "midpoint"

    average, detail = _rule_derived_value(
        {"operation": "average", "input_positions": [2, 3, 5, 6]},
        records,
        "melting_point_c",
    )
    assert math.isclose(average, 1449.5975)
    assert detail == "average"

    interval, detail = _rule_derived_value(
        {"operation": "addition_with_previous_interval", "input_positions": [2, 3]},
        records,
        "density_g_cm3",
    )
    assert math.isclose(interval, 2.3992)
    assert detail == "addition with previous interval"


def test_rediscovery_diagnostic_does_not_guess_unsupported_or_unavailable_rules():
    from scripts.accept_ollama_rediscovery import _rule_derived_value
    from episteme.rediscovery import build_mendeleev_fixture

    records = build_mendeleev_fixture().pre_discovery_records

    value, detail = _rule_derived_value(
        {"operation": "midpoint", "input_positions": [3, 4]},
        records,
        "relative_atomic_mass",
    )
    assert value is None
    assert "not available" in detail

    value, detail = _rule_derived_value(
        {"operation": "polynomial_extrapolation", "input_positions": [2, 3]},
        records,
        "relative_atomic_mass",
    )
    assert value is None
    assert "unsupported operation" in detail



def test_phase29_acceptance_requires_forecast_to_match_a_host_computed_source_rule():
    from types import SimpleNamespace
    from scripts.accept_ollama_rediscovery import _forecast_matches_source_rule

    fixture = build_mendeleev_fixture()
    prediction = SimpleNamespace(
        id="prediction-1",
        source_id="hypothesis-1",
        predicted_numeric_value=73.3975,
    )
    hypotheses = {
        "hypothesis-1": {
            "quantitative_rule": {
                "operation": "midpoint",
                "property": "property_P",
                "input_positions": [3, 5],
            }
        }
    }

    assert _forecast_matches_source_rule(
        prediction, hypotheses, fixture.pre_discovery_records,
        "relative_atomic_mass", "property_P",
    )

    hypotheses["hypothesis-1"]["quantitative_rule"]["operation"] = "gap_fill"
    assert not _forecast_matches_source_rule(
        prediction, hypotheses, fixture.pre_discovery_records,
        "relative_atomic_mass", "property_P",
    )


def test_phase29_runtime_validator_accepts_correct_rule_forecast_without_reading_held_out_record():
    from types import SimpleNamespace
    from scripts.accept_ollama_rediscovery import _validate_numeric_prediction_action
    from episteme.autonomy import DiscoveryAction
    from episteme.store import Store

    fixture = build_mendeleev_fixture()
    hypothesis = SimpleNamespace(
        id="hypothesis-one",
        quantitative_rule={
            "operation": "midpoint",
            "property": "property_P",
            "input_positions": [3, 5],
        },
    )
    with Store() as store:
        for record in fixture.pre_discovery_records + (fixture.held_out_record,):
            store.put_record(record)
        store.iter_hypotheses = lambda: iter((hypothesis,))
        action = DiscoveryAction(
            kind="prediction",
            target_ids=(hypothesis.id,),
            conditions="bounded historical fixture",
            consequence="numeric forecast",
            predicted_numeric_values={hypothesis.id: 73.3975},
            rationale="arithmetic follows the declared midpoint rule",
        )
        _validate_numeric_prediction_action(
            store,
            action,
            tuple(record.id for record in fixture.pre_discovery_records),
            property_key="relative_atomic_mass",
            expected_rule_property="property_P",
        )


def test_phase29_runtime_validator_rejects_wrong_forecast_with_corrective_feedback():
    import pytest
    from types import SimpleNamespace
    from scripts.accept_ollama_rediscovery import _validate_numeric_prediction_action
    from episteme.autonomy import DiscoveryAction, PlannerActionError
    from episteme.store import Store

    fixture = build_mendeleev_fixture()
    hypothesis = SimpleNamespace(
        id="hypothesis-one",
        quantitative_rule={
            "operation": "midpoint",
            "property": "property_P",
            "input_positions": [3, 5],
        },
    )
    with Store() as store:
        for record in fixture.pre_discovery_records:
            store.put_record(record)
        store.iter_hypotheses = lambda: iter((hypothesis,))
        action = DiscoveryAction(
            kind="prediction",
            target_ids=(hypothesis.id,),
            conditions="bounded historical fixture",
            consequence="numeric forecast",
            predicted_numeric_values={hypothesis.id: 42.0},
            rationale="deliberately incorrect forecast",
        )
        with pytest.raises(PlannerActionError, match=r"proposed 42.*computes 73.3975"):
            _validate_numeric_prediction_action(
                store,
                action,
                tuple(record.id for record in fixture.pre_discovery_records),
                property_key="relative_atomic_mass",
                expected_rule_property="property_P",
            )


def test_phase29_runtime_validator_fails_closed_for_unavailable_rule_inputs():
    import pytest
    from types import SimpleNamespace
    from scripts.accept_ollama_rediscovery import _validate_numeric_prediction_action
    from episteme.autonomy import DiscoveryAction, PlannerActionError
    from episteme.store import Store

    fixture = build_mendeleev_fixture()
    hypothesis = SimpleNamespace(
        id="hypothesis-one",
        quantitative_rule={
            "operation": "midpoint",
            "property": "property_P",
            "input_positions": [3, 4],
        },
    )
    with Store() as store:
        for record in fixture.pre_discovery_records:
            store.put_record(record)
        store.iter_hypotheses = lambda: iter((hypothesis,))
        action = DiscoveryAction(
            kind="prediction",
            target_ids=(hypothesis.id,),
            conditions="bounded historical fixture",
            consequence="numeric forecast",
            predicted_numeric_values={hypothesis.id: 42.0},
            rationale="unavailable rule input test",
        )
        with pytest.raises(PlannerActionError, match="cannot be verified from permitted pre-discovery"):
            _validate_numeric_prediction_action(
                store,
                action,
                tuple(record.id for record in fixture.pre_discovery_records),
                property_key="relative_atomic_mass",
                expected_rule_property="property_P",
            )


def test_phase29_runtime_validator_rejects_untrusted_property_mapping():
    import pytest
    from types import SimpleNamespace
    from scripts.accept_ollama_rediscovery import _validate_numeric_prediction_action
    from episteme.autonomy import DiscoveryAction, PlannerActionError
    from episteme.store import Store

    fixture = build_mendeleev_fixture()
    hypothesis = SimpleNamespace(
        id="hypothesis-one",
        quantitative_rule={
            "operation": "midpoint",
            "property": "relative_atomic_mass",
            "input_positions": [3, 5],
        },
    )
    with Store() as store:
        for record in fixture.pre_discovery_records:
            store.put_record(record)
        store.iter_hypotheses = lambda: iter((hypothesis,))
        action = DiscoveryAction(
            kind="prediction",
            target_ids=(hypothesis.id,),
            conditions="blinded historical fixture",
            consequence="numeric forecast",
            predicted_numeric_values={hypothesis.id: 73.3975},
            rationale="mapping must be host-controlled",
        )
        with pytest.raises(PlannerActionError, match="no verified rule for host-mapped property"):
            _validate_numeric_prediction_action(
                store,
                action,
                tuple(record.id for record in fixture.pre_discovery_records),
                property_key="relative_atomic_mass",
                expected_rule_property="property_P",
            )


def test_phase29_acceptance_rejects_forecast_that_disagrees_with_its_source_rule():
    from types import SimpleNamespace
    from scripts.accept_ollama_rediscovery import _forecast_matches_source_rule

    fixture = build_mendeleev_fixture()
    prediction = SimpleNamespace(
        id="prediction-1",
        source_id="hypothesis-1",
        predicted_numeric_value=999.0,
    )
    hypotheses = {
        "hypothesis-1": {
            "quantitative_rule": {
                "operation": "midpoint",
                "property": "property_P",
                "input_positions": [3, 5],
            }
        }
    }

    assert not _forecast_matches_source_rule(
        prediction, hypotheses, fixture.pre_discovery_records,
        "relative_atomic_mass", "property_P",
    )
