import json

from episteme.autonomy import DiscoveryContext
from episteme.ollama import OllamaPlanner


def test_ollama_planner_translates_structured_model_output():
    captured = {}

    def transport(payload):
        captured.update(payload)
        return {
            "message": {
                "content": json.dumps(
                    {
                        "kind": "stop",
                        "rationale": "The next step requires external evidence.",
                    }
                )
            }
        }

    planner = OllamaPlanner("qwen3:8b", transport=transport)
    context = DiscoveryContext(
        grounded_input_ids=("grounded-1",),
        findings=(),
        hypotheses=(),
        predictions=(),
        experiments=(),
        actions_taken=(),
    )

    action = planner.choose(context)

    assert action.kind == "stop"
    assert "external evidence" in action.rationale
    assert captured["model"] == "qwen3:8b"
    assert captured["stream"] is False
    assert captured["format"]["type"] == "object"
    assert captured["format"]["additionalProperties"] is False
    assert "rationale" in captured["format"]["properties"]
    assert captured["format"]["required"] == ["kind", "rationale"]
    assert captured["format"]["properties"]["kind"]["enum"] == [
        "scout",
        "assess_exploration",
        "admit_exploration",
        "discover_gap",
        "question",
        "hypothesis",
        "prediction",
        "experiment",
        "request_evidence",
        "stop",
    ]
    assert len(captured["format"]["oneOf"]) == 10

    schemas_by_kind = {
        schema["properties"]["kind"]["const"]: schema
        for schema in captured["format"]["oneOf"]
    }
    prediction_schema = schemas_by_kind["prediction"]
    assert "conditions" in prediction_schema["required"]
    assert "consequence" in prediction_schema["required"]
    assert "consequences" not in prediction_schema["required"]
    assert "oneOf" not in prediction_schema

    request_schema = schemas_by_kind["request_evidence"]
    assert {"target_ids", "evidence_capability", "evidence_parameters", "requested_representation"}.issubset(request_schema["required"])

    experiment_schema = schemas_by_kind["experiment"]
    assert {
        "conditions",
        "objective",
        "proposed_observation",
        "discrimination_basis",
    }.issubset(experiment_schema["required"])
    assert captured["messages"][0]["role"] == "system"


def test_ollama_planner_rejects_malformed_model_action():
    def transport(payload):
        return {"message": {"content": json.dumps({"kind": "teleport", "rationale": "nope"})}}

    planner = OllamaPlanner("fixture", transport=transport)
    context = DiscoveryContext((), (), (), (), (), ())

    try:
        planner.choose(context)
    except ValueError as exc:
        assert "invalid DiscoveryAction" in str(exc)
    else:
        raise AssertionError("malformed model action was accepted")
