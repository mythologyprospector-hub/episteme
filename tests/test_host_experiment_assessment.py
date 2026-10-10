from types import SimpleNamespace

from episteme.autonomy import _evaluations_produced_by_run, _host_experiment_assessment


def _evaluations(*outcomes):
    return tuple(SimpleNamespace(outcome=outcome) for outcome in outcomes)


def test_host_assessment_marks_mixed_outcomes_unresolved():
    summary = _host_experiment_assessment(_evaluations("consistent", "inconsistent"))
    assert "outcomes are mixed" in summary
    assert "1 consistent, 1 inconsistent, 0 unresolved" in summary
    assert "not evaluation evidence" in summary


def test_host_assessment_marks_all_inconsistent_as_contradicted():
    summary = _host_experiment_assessment(_evaluations("inconsistent", "inconsistent"))
    assert "all evaluated predictions are contradicted" in summary
    assert "0 consistent, 2 inconsistent, 0 unresolved" in summary


def test_host_assessment_distinguishes_consistency_from_truth():
    summary = _host_experiment_assessment(_evaluations("consistent", "consistent"))
    assert "all evaluated predictions are consistent" in summary
    assert "Consistency is not proof of truth" in summary


def test_host_assessment_does_not_overstate_unresolved_outcomes():
    summary = _host_experiment_assessment(_evaluations("unresolved", "consistent"))
    assert "does not resolve the predictions" in summary
    assert "1 consistent, 0 inconsistent, 1 unresolved" in summary


def test_host_assessment_handles_missing_evaluations():
    summary = _host_experiment_assessment(())
    assert summary == "Host assessment: no prediction evaluations are available."


def test_evaluations_produced_by_run_excludes_historical_evaluations():
    historical = SimpleNamespace(id="historical-evaluation")
    current = SimpleNamespace(id="current-evaluation")
    store = SimpleNamespace(iter_prediction_evaluations=lambda: (historical, current))
    steps = (SimpleNamespace(output_ids=("proposal-id", "current-evaluation", "result-id")),)

    assert _evaluations_produced_by_run(store, list(steps)) == (current,)
    assert _evaluations_produced_by_run(store, []) == ()


def test_stop_reason_does_not_mislabel_historical_evaluations(monkeypatch):
    from episteme.autonomy import DiscoveryAction, run_autonomous_discovery
    from episteme.model import PredictionEvaluationOutcome
    from episteme.store import Store

    evaluation = SimpleNamespace(
        id="evaluation-1",
        result_id="result-1",
        prediction_id="prediction-1",
        experiment_proposal_id=None,
        comparison_conditions="integration-test conditions",
        assumptions=(),
        outcome=PredictionEvaluationOutcome.INCONSISTENT,
        rationale="integration-test evaluation",
        method="integration-test",
        method_version="1",
        created_at="2026-10-05T00:00:00Z",
    )

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
    assert "Host-derived experiment assessment" not in result.stop_reason
