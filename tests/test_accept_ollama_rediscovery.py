def test_prediction_diagnostics_link_forecast_to_source_rule_and_evaluation():
    from episteme.model import PredictionEvaluationOutcome

    prediction = SimpleNamespace(
        id="prediction-123",
        source_id="11111111-1111-4111-8111-111111111111",
        comparison_hypothesis_ids=("11111111-1111-4111-8111-111111111111", "22222222-2222-4222-8222-222222222222"),
        predicted_numeric_value=5.3197,
        rationale="(7.287 - 2.3296) + 2.3296 = 7.287",
    )
    hypotheses = {
        "11111111-1111-4111-8111-111111111111": {
            "id": "11111111-1111-4111-8111-111111111111",
            "statement": "Extrapolate the prior density difference.",
            "quantitative_rule": {"operation": "linear_extrapolation"},
        },
        "22222222-2222-4222-8222-222222222222": {
            "id": "22222222-2222-4222-8222-222222222222",
            "statement": "Use the adjacent midpoint.",
            "quantitative_rule": {"operation": "midpoint"},
        },
    }
    evaluations = {
        prediction.id: SimpleNamespace(
            outcome=PredictionEvaluationOutcome.CONSISTENT,
            rationale="forecast matches the executed result",
        )
    }

    from episteme.rediscovery import build_mendeleev_fixture
    from scripts.accept_ollama_rediscovery import _prediction_diagnostic_lines

    fixture = build_mendeleev_fixture()
    lines = _prediction_diagnostic_lines(
        (prediction,), evaluations, hypotheses,
        fixture.pre_discovery_records, "density_g_cm3",
    )
    output = "\\n".join(lines)

    assert "source_hypothesis=11111111" in output
    assert "linear_extrapolation" in output
    assert "model-authored rationale (not independently verified):" in output
    assert "host rule check: UNVERIFIED" in output
    assert "evaluator verdict: consistent" in output
    assert "22222222" in output


import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.accept_ollama_rediscovery import (
    _at_least_one_forecast_consistent,
    _contains_blinded_element_name,
    _index_evaluations,
    _validate_experiment_evidence,
)


def test_evaluations_are_associated_by_prediction_id_not_list_order():
    predictions = (SimpleNamespace(id="p1"), SimpleNamespace(id="p2"))
    evaluation_for_p1 = SimpleNamespace(prediction_id="p1", outcome="consistent")
    evaluation_for_p2 = SimpleNamespace(prediction_id="p2", outcome="inconsistent")

    indexed, integrity_ok = _index_evaluations(
        predictions,
        (evaluation_for_p2, evaluation_for_p1),
    )

    assert integrity_ok
    assert indexed["p1"] is evaluation_for_p1
    assert indexed["p2"] is evaluation_for_p2


def test_evaluation_index_rejects_missing_or_duplicate_evaluation_records():
    predictions = (SimpleNamespace(id="p1"), SimpleNamespace(id="p2"))
    one_evaluation = SimpleNamespace(prediction_id="p1", outcome="consistent")
    duplicate_evaluation = SimpleNamespace(prediction_id="p1", outcome="inconsistent")

    _, missing_ok = _index_evaluations(predictions, (one_evaluation,))
    _, duplicate_ok = _index_evaluations(predictions, (one_evaluation, duplicate_evaluation))

    assert not missing_ok
    assert not duplicate_ok


def test_blinded_name_check_uses_whole_words_not_substrings():
    assert not _contains_blinded_element_name("The hypotheses propose distinct quantitative forecasts.")
    assert not _contains_blinded_element_name("The inquiry continues with the current predictions.")
    assert _contains_blinded_element_name("The missing element may be tin.")
    assert _contains_blinded_element_name("The observations mention silicon and germanium.")



def test_experiment_evidence_requires_matching_persisted_result_and_proposal():
    prediction = SimpleNamespace(id="p1", predicted_numeric_value=73.4)
    evaluation = SimpleNamespace(
        prediction_id="p1", result_id="r1", experiment_proposal_id="e1"
    )
    result = SimpleNamespace(
        id="r1",
        payload={
            "executor": "phase29_rediscovery",
            "property_key": "relative_atomic_mass",
            "input_ids": ["held-out"],
            "experiment_proposal_id": "e1",
        },
    )
    proposal = SimpleNamespace(id="e1", prediction_ids=("p1",))

    class FakeStore:
        def iter_records(self, kind=None):
            assert kind == "result"
            return iter((result,))

        def get_experiment_proposal(self, proposal_id):
            return proposal if proposal_id == "e1" else None

    assert _validate_experiment_evidence(
        FakeStore(), (prediction,), (evaluation,), "held-out", "relative_atomic_mass"
    )


def test_experiment_evidence_rejects_wrong_scope_or_unlinked_evaluation():
    prediction = SimpleNamespace(id="p1", predicted_numeric_value=73.4)
    evaluation = SimpleNamespace(
        prediction_id="p1", result_id="other-result", experiment_proposal_id="e1"
    )
    result = SimpleNamespace(
        id="r1",
        payload={
            "executor": "phase29_rediscovery",
            "property_key": "relative_atomic_mass",
            "input_ids": ["not-held-out"],
            "experiment_proposal_id": "e1",
        },
    )
    proposal = SimpleNamespace(id="e1", prediction_ids=("p1",))

    class FakeStore:
        def iter_records(self, kind=None):
            return iter((result,))

        def get_experiment_proposal(self, proposal_id):
            return proposal

    assert not _validate_experiment_evidence(
        FakeStore(), (prediction,), (evaluation,), "held-out", "relative_atomic_mass"
    )


def test_experiment_evidence_rejects_non_finite_forecasts():
    prediction = SimpleNamespace(id="p1", predicted_numeric_value=float("nan"))

    class FakeStore:
        def iter_records(self, kind=None):
            return iter(())

        def get_experiment_proposal(self, proposal_id):
            return None

    assert not _validate_experiment_evidence(
        FakeStore(), (prediction,), (), "held-out", "relative_atomic_mass"
    )



def test_one_consistent_forecast_can_satisfy_competing_forecast_gate():
    from episteme.model import PredictionEvaluationOutcome

    predictions = (
        SimpleNamespace(id="p1"),
        SimpleNamespace(id="p2"),
    )
    evaluations = (
        SimpleNamespace(prediction_id="p1", outcome=PredictionEvaluationOutcome.CONSISTENT),
        SimpleNamespace(prediction_id="p2", outcome=PredictionEvaluationOutcome.INCONSISTENT),
    )

    assert _at_least_one_forecast_consistent(predictions, evaluations)


def test_all_consistent_forecasts_also_satisfy_competing_forecast_gate():
    from episteme.model import PredictionEvaluationOutcome

    predictions = (SimpleNamespace(id="p1"), SimpleNamespace(id="p2"))
    evaluations = (
        SimpleNamespace(prediction_id="p1", outcome=PredictionEvaluationOutcome.CONSISTENT),
        SimpleNamespace(prediction_id="p2", outcome=PredictionEvaluationOutcome.CONSISTENT),
    )

    assert _at_least_one_forecast_consistent(predictions, evaluations)


def test_competing_forecast_gate_fails_when_no_forecast_is_consistent():
    from episteme.model import PredictionEvaluationOutcome

    predictions = (SimpleNamespace(id="p1"), SimpleNamespace(id="p2"))
    evaluations = (
        SimpleNamespace(prediction_id="p1", outcome=PredictionEvaluationOutcome.INCONSISTENT),
        SimpleNamespace(prediction_id="p2", outcome=PredictionEvaluationOutcome.INCONSISTENT),
    )

    assert not _at_least_one_forecast_consistent(predictions, evaluations)
