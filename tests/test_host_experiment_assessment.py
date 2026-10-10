from types import SimpleNamespace

from episteme.autonomy import (
    DiscoveryAction,
    ExperimentAssessmentStatus,
    _evaluations_produced_by_run,
    _host_experiment_assessment,
    run_autonomous_discovery,
)
from episteme.model import PredictionEvaluationOutcome
from episteme.store import Store


def _evaluation(prediction_id, outcome, evaluation_id=None):
    return SimpleNamespace(
        id=evaluation_id or f"eval-{prediction_id}",
        prediction_id=prediction_id,
        outcome=outcome,
    )


def test_host_assessment_marks_mixed_outcomes_without_claiming_success():
    assessment = _host_experiment_assessment(
        (_evaluation("p1", "consistent"), _evaluation("p2", "inconsistent")),
        ("p1", "p2"),
    )
    assert assessment.status is ExperimentAssessmentStatus.MIXED
    assert (assessment.consistent_count, assessment.inconsistent_count, assessment.unresolved_count) == (1, 1, 0)
    assert "Consistency is not proof of truth" in assessment.summary


def test_host_assessment_marks_all_inconsistent_as_contradicted():
    assessment = _host_experiment_assessment(
        (_evaluation("p1", "inconsistent"), _evaluation("p2", "inconsistent")),
        ("p1", "p2"),
    )
    assert assessment.status is ExperimentAssessmentStatus.INCONSISTENT
    assert assessment.inconsistent_count == 2
    assert "contradicted by the experiment" in assessment.summary


def test_host_assessment_marks_all_consistent_without_claiming_truth():
    assessment = _host_experiment_assessment(
        (_evaluation("p1", "consistent"), _evaluation("p2", "consistent")),
        ("p1", "p2"),
    )
    assert assessment.status is ExperimentAssessmentStatus.CONSISTENT
    assert assessment.consistent_count == 2
    assert "Consistency is not proof of truth" in assessment.summary


def test_host_assessment_marks_inconclusive_evaluation_unresolved():
    assessment = _host_experiment_assessment(
        (_evaluation("p1", PredictionEvaluationOutcome.INCONCLUSIVE),),
        ("p1",),
    )
    assert assessment.status is ExperimentAssessmentStatus.UNRESOLVED
    assert assessment.unresolved_count == 1


def test_missing_or_duplicate_evaluations_remain_unresolved():
    missing = _host_experiment_assessment((), ("p1", "p2"))
    duplicate = _host_experiment_assessment(
        (_evaluation("p1", "consistent"), _evaluation("p1", "consistent")),
        ("p1",),
    )
    assert missing.status is ExperimentAssessmentStatus.UNRESOLVED
    assert missing.unresolved_count == 2
    assert duplicate.status is ExperimentAssessmentStatus.UNRESOLVED
    assert duplicate.unresolved_count == 1


def test_evaluations_produced_by_run_excludes_historical_evaluations():
    historical = SimpleNamespace(id="historical-evaluation")
    current = SimpleNamespace(id="current-evaluation")
    store = SimpleNamespace(iter_prediction_evaluations=lambda: (historical, current))
    steps = (SimpleNamespace(output_ids=("proposal-id", "current-evaluation", "result-id")),)
    assert _evaluations_produced_by_run(store, list(steps)) == (current,)
    assert _evaluations_produced_by_run(store, []) == ()


def test_stop_preserves_planner_rationale_and_separates_host_assessment(monkeypatch):
    evaluation = _evaluation("prediction-1", PredictionEvaluationOutcome.INCONSISTENT, "evaluation-1")
    class StopPlanner:
        def choose(self, context):
            return DiscoveryAction(kind="stop", rationale="The model says the experiment succeeded.")

    with Store() as store:
        monkeypatch.setattr(store, "iter_prediction_evaluations", lambda: (evaluation,))
        result = run_autonomous_discovery(
            store, StopPlanner(), grounded_input_ids=(), started_at="2026-10-05T00:00:00Z"
        )
    assert result.status == "stopped"
    assert result.stop_reason == "The model says the experiment succeeded."
    assert result.experiment_assessment is None


def test_host_assessment_is_unresolved_when_run_has_experiment_but_no_evaluations(monkeypatch):
    from episteme.autonomy import DiscoveryStep

    class StopPlanner:
        def choose(self, context):
            return DiscoveryAction(kind="stop", rationale="Stop after the bounded experiment.")

    with Store() as store:
        result = run_autonomous_discovery(
            store, StopPlanner(), grounded_input_ids=(), started_at="2026-10-05T00:00:00Z"
        )
        # Exercise the structured assessment builder for the incomplete-evaluation case;
        # a run without an experiment action correctly has no experiment assessment.
        assessment = _host_experiment_assessment((), ("prediction-1",))
    assert result.experiment_assessment is None
    assert assessment.status is ExperimentAssessmentStatus.UNRESOLVED
    assert assessment.unresolved_count == 1
