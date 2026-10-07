import json

import pytest

from episteme.autonomy import DiscoveryContext, DiscoveryAction, PlannerActionError
from episteme.ollama import OllamaPlanner


def _context():
    return DiscoveryContext(
        grounded_input_ids=(),
        findings=(),
        hypotheses=(),
        predictions=(),
        experiments=(),
        actions_taken=(),
    )


def _planner(content):
    def transport(_payload):
        return {"message": {"content": content}}

    return OllamaPlanner("qwen3:8b", transport=transport)


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("not json", "invalid JSON"),
        ("[]", "must be an object"),
        ('{"kind":"stop"}', "invalid DiscoveryAction"),
        ('{"kind":"stop","rationale":"ok","unexpected":"nope"}', "invalid DiscoveryAction"),
    ],
)
def test_ollama_rejects_invalid_action_payloads(content, expected):
    with pytest.raises(PlannerActionError, match=expected):
        _planner(content).choose(_context())


def test_ollama_accepts_only_bounded_action_fields():
    action = _planner(
        json.dumps(
            {
                "kind": "stop",
                "rationale": "The bounded investigation requires new grounded evidence.",
            }
        )
    ).choose(_context())

    assert isinstance(action, DiscoveryAction)
    assert action.kind == "stop"
    assert action.rationale.startswith("The bounded investigation")


def test_ollama_schema_exposes_request_evidence_action():
    payload = {}

    def transport(request):
        payload.update(request)
        return {
            "message": {
                "content": json.dumps(
                    {
                        "kind": "request_evidence",
                        "target_ids": ["prediction-1"],
                        "evidence_capability": "crossref_works",
                        "evidence_parameters": {"query.title": "test"},
                        "requested_representation": "application/json",
                        "rationale": "Additional evidence is required to discriminate the active alternatives.",
                    }
                )
            }
        }

    action = OllamaPlanner("qwen3:8b", transport=transport, evidence_capabilities=("crossref_works",)).choose(_context())

    assert action.kind == "request_evidence"
    assert action.evidence_capability == "crossref_works"
    assert action.requested_representation == "application/json"
    assert "available_evidence_capabilities" in payload["messages"][1]["content"]
    assert "crossref_works" in payload["messages"][1]["content"]
    assert "application/json" in payload["messages"][1]["content"]
    assert "query.title" in payload["messages"][1]["content"]
    schema = payload["format"]
    assert "request_evidence" in schema["properties"]["kind"]["enum"]
    assert "evidence_capability" in schema["properties"]
    assert "evidence_parameters" in schema["properties"]
    assert "requested_representation" in schema["properties"]


def test_ollama_prediction_schema_exposes_required_typed_fields():
    payload = {}

    def transport(request):
        payload.update(request)
        return {
            "message": {
                "content": json.dumps(
                    {
                        "kind": "prediction",
                        "target_ids": ["hypothesis-1", "hypothesis-2"],
                        "conditions": "Under the bounded fixture conditions.",
                        "consequence": "The predicted position is present.",
                        "expected_presences": {
                            "hypothesis-1": True,
                            "hypothesis-2": False,
                        },
                        "rationale": "The competing hypotheses require a discriminating prediction.",
                    }
                )
            }
        }

    action = OllamaPlanner("qwen3:8b", transport=transport).choose(_context())

    assert action.kind == "prediction"
    assert action.conditions == "Under the bounded fixture conditions."
    assert action.expected_presences == {
        "hypothesis-1": True,
        "hypothesis-2": False,
    }
    schema = payload["format"]
    assert "expected_presences" in schema["properties"]
    prediction_branch = next(
        branch
        for branch in schema["oneOf"]
        if branch["properties"]["kind"]["const"] == "prediction"
    )
    assert "expected_presences" in prediction_branch["required"]
