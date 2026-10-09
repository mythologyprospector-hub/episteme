import json

from episteme.autonomy import DiscoveryContext
from episteme.ollama import OllamaPlanner


def test_ollama_context_includes_deterministic_evaluations_and_consequences():
    context = DiscoveryContext(
        grounded_input_ids=(),
        findings=(),
        hypotheses=(),
        predictions=({"id": "prediction-a"}, {"id": "prediction-b"}),
        experiments=({"id": "experiment-a"},),
        actions_taken=(),
        evaluations=(
            {
                "id": "evaluation-a",
                "result_id": "result-a",
                "prediction_id": "prediction-a",
                "experiment_proposal_id": "experiment-a",
                "outcome": "consistent",
            },
            {
                "id": "evaluation-b",
                "result_id": "result-a",
                "prediction_id": "prediction-b",
                "experiment_proposal_id": "experiment-a",
                "outcome": "inconsistent",
            },
        ),
        consequences=(
            {
                "id": "consequence-a",
                "evaluation_ids": ("evaluation-a",),
                "target_kind": "prediction",
                "target_id": "prediction-a",
                "consequence": "supports",
            },
            {
                "id": "consequence-b",
                "evaluation_ids": ("evaluation-b",),
                "target_kind": "prediction",
                "target_id": "prediction-b",
                "consequence": "contradicts",
            },
        ),
    )

    payload = OllamaPlanner("qwen3:8b")._request_payload(context)
    planner_context = json.loads(payload["messages"][1]["content"])

    assert planner_context["evaluations"] == [
        {
            "id": "evaluation-a",
            "result_id": "result-a",
            "prediction_id": "P1",
            "experiment_proposal_id": "X1",
            "outcome": "consistent",
        },
        {
            "id": "evaluation-b",
            "result_id": "result-a",
            "prediction_id": "P2",
            "experiment_proposal_id": "X1",
            "outcome": "inconsistent",
        },
    ]
    assert planner_context["consequences"] == [
        {
            "id": "consequence-a",
            "evaluation_ids": ["evaluation-a"],
            "target_kind": "prediction",
            "target_id": "P1",
            "consequence": "supports",
        },
        {
            "id": "consequence-b",
            "evaluation_ids": ["evaluation-b"],
            "target_kind": "prediction",
            "target_id": "P2",
            "consequence": "contradicts",
        },
    ]
    assert "deterministic host evidence" in payload["messages"][0]["content"]
