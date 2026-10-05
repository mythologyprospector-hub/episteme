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
    assert captured["format"] == "json"
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
