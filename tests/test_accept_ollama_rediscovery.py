import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.accept_ollama_rediscovery import (
    _all_forecasts_consistent,
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



def test_one_consistent_forecast_cannot_mask_an_inconsistent_forecast():
    predictions = (
        SimpleNamespace(id="p1"),
        SimpleNamespace(id="p2"),
    )
    evaluations = (
        SimpleNamespace(prediction_id="p1", outcome=__import__(
            "episteme.model", fromlist=["PredictionEvaluationOutcome"]
        ).PredictionEvaluationOutcome.CONSISTENT),
        SimpleNamespace(prediction_id="p2", outcome=__import__(
            "episteme.model", fromlist=["PredictionEvaluationOutcome"]
        ).PredictionEvaluationOutcome.INCONSISTENT),
    )

    assert not _all_forecasts_consistent(predictions, evaluations)


def test_all_forecasts_must_have_consistent_evaluations():
    from episteme.model import PredictionEvaluationOutcome

    predictions = (SimpleNamespace(id="p1"), SimpleNamespace(id="p2"))
    evaluations = (
        SimpleNamespace(prediction_id="p1", outcome=PredictionEvaluationOutcome.CONSISTENT),
        SimpleNamespace(prediction_id="p2", outcome=PredictionEvaluationOutcome.CONSISTENT),
    )

    assert _all_forecasts_consistent(predictions, evaluations)
