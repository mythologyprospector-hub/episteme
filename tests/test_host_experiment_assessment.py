from types import SimpleNamespace

from episteme.autonomy import _host_experiment_assessment


def _evaluations(*outcomes):
    return tuple(SimpleNamespace(outcome=outcome) for outcome in outcomes)


def test_host_assessment_marks_mixed_outcomes_unresolved():
    summary = _host_experiment_assessment(
        _evaluations("consistent", "inconsistent")
    )

    assert "outcomes are mixed" in summary
    assert "1 consistent, 1 inconsistent, 0 unresolved" in summary
    assert "not evaluation evidence" in summary


def test_host_assessment_marks_all_inconsistent_as_contradicted():
    summary = _host_experiment_assessment(
        _evaluations("inconsistent", "inconsistent")
    )

    assert "all evaluated predictions are contradicted" in summary
    assert "0 consistent, 2 inconsistent, 0 unresolved" in summary


def test_host_assessment_distinguishes_consistency_from_truth():
    summary = _host_experiment_assessment(
        _evaluations("consistent", "consistent")
    )

    assert "all evaluated predictions are consistent" in summary
    assert "Consistency is not proof of truth" in summary


def test_host_assessment_does_not_overstate_unresolved_outcomes():
    summary = _host_experiment_assessment(
        _evaluations("unresolved", "consistent")
    )

    assert "does not resolve the predictions" in summary
    assert "1 consistent, 0 inconsistent, 1 unresolved" in summary


def test_host_assessment_handles_missing_evaluations():
    summary = _host_experiment_assessment(())

    assert summary == "Host assessment: no prediction evaluations are available."
