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
