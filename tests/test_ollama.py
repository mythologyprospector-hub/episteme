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
                        "target_ids": ["P1"],
                        "evidence_capability": "crossref_works",
                        "evidence_parameters": {"query.title": "test"},
                        "requested_representation": "application/json",
                        "rationale": "Additional evidence is required to discriminate the active alternatives.",
                    }
                )
            }
        }

    evidence_context = DiscoveryContext(
        grounded_input_ids=(),
        findings=(),
        hypotheses=(),
        predictions=({"id": "prediction-1"},),
        experiments=({"id": "experiment-1"},),
        actions_taken=(),
    )
    action = OllamaPlanner("qwen3:8b", transport=transport, evidence_capabilities=("crossref_works",)).choose(evidence_context)

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
                        "target_ids": ["H1", "H2"],
                        "conditions": "Under the bounded fixture conditions.",
                        "consequence": "The predicted position is present.",
                        "expected_presences": {
                            "H1": True,
                            "H2": False,
                        },
                        "predicted_numeric_value": 73.4,
                        "rationale": "The competing hypotheses require a discriminating prediction.",
                    }
                )
            }
        }

    prediction_context = DiscoveryContext(
        grounded_input_ids=(),
        findings=(),
        hypotheses=(
            {"id": "hypothesis-1"},
            {"id": "hypothesis-2"},
        ),
        predictions=(),
        experiments=(),
        actions_taken=(),
    )
    action = OllamaPlanner("qwen3:8b", transport=transport).choose(prediction_context)

    assert action.kind == "prediction"
    assert action.conditions == "Under the bounded fixture conditions."
    assert action.expected_presences == {
        "hypothesis-1": True,
        "hypothesis-2": False,
    }
    schema = payload["format"]
    assert "expected_presences" in schema["properties"]
    assert schema["properties"]["expected_presences"]["type"] == "object"
    assert schema["properties"]["expected_presences"]["additionalProperties"] is False
    assert schema["properties"]["expected_presences"]["required"] == ["H1", "H2"]
    assert "oneOf" not in schema
    assert schema["required"] == [
        "kind",
        "rationale",
        "target_ids",
        "conditions",
        "consequence",
        "expected_presences",
        "predicted_numeric_value",
    ]



def test_ollama_rejects_duplicate_planner_handles():
    context = DiscoveryContext(
        grounded_input_ids=(),
        findings=(),
        hypotheses=(
            {"id": "hypothesis-1"},
            {"id": "hypothesis-2"},
        ),
        predictions=(),
        experiments=(),
        actions_taken=(),
    )
    with pytest.raises(PlannerActionError, match="duplicate planner handles"):
        _planner(
            json.dumps({
                "kind": "prediction",
                "target_ids": ["H1", "H1"],
                "conditions": "bounded",
                "consequence": "test",
                "expected_presences": {"H1": True},
                "rationale": "The competing hypotheses require a discriminating prediction.",
            })
        ).choose(context)


def test_ollama_experiment_schema_exposes_required_typed_fields():
    payload = {}

    def transport(request):
        payload.update(request)
        return {
            "message": {
                "content": json.dumps(
                    {
                        "kind": "experiment",
                        "target_ids": ["P1", "P2"],
                        "conditions": "Under the bounded held-out fixture conditions.",
                        "objective": "Discriminate the competing predictions.",
                        "proposed_observation": "Observe whether the held-out position is present.",
                        "discrimination_basis": "The competing predictions disagree at the held-out position.",
                        "execution_spec": {
                            "operation": "positional_presence",
                            "position": 3.0,
                        },
                        "rationale": "The competing predictions require a bounded discriminating experiment.",
                    }
                )
            }
        }

    experiment_context = DiscoveryContext(
        grounded_input_ids=(),
        findings=(),
        hypotheses=(),
        predictions=(
            {"id": "prediction-1"},
            {"id": "prediction-2"},
        ),
        experiments=(),
        actions_taken=(),
    )
    action = OllamaPlanner("qwen3:8b", transport=transport).choose(experiment_context)

    assert action.kind == "experiment"
    assert action.execution_spec == {
        "operation": "positional_presence",
        "position": 3.0,
    }
    schema = payload["format"]
    assert schema["required"] == [
        "kind",
        "rationale",
        "target_ids",
        "conditions",
        "objective",
        "proposed_observation",
        "discrimination_basis",
        "execution_spec",
    ]
    assert "position_key" not in schema["properties"]["execution_spec"]["properties"]



def test_ollama_historical_rediscovery_schema_restricts_execution_operation():
    payload = {}

    def transport(request):
        payload.update(request)
        return {
            "message": {
                "content": json.dumps(
                    {
                        "kind": "experiment",
                        "target_ids": ["P1", "P2"],
                        "conditions": "Under bounded historical conditions.",
                        "objective": "Discriminate the numeric forecasts.",
                        "proposed_observation": "Observe the held-out property.",
                        "discrimination_basis": "The forecasts differ.",
                        "execution_spec": {"operation": "historical_rediscovery"},
                        "rationale": "A bounded historical experiment is required.",
                    }
                )
            }
        }

    context = DiscoveryContext(
        grounded_input_ids=(),
        findings=(),
        hypotheses=(),
        predictions=(
            {"id": "prediction-1"},
            {"id": "prediction-2"},
        ),
        experiments=(),
        actions_taken=(),
    )
    action = OllamaPlanner(
        "gemma3:12b-it-q4_K_M",
        transport=transport,
        host_capabilities=("historical_rediscovery",),
    ).choose(context)

    assert action.execution_spec == {"operation": "historical_rediscovery"}
    execution_schema = payload["format"]["properties"]["execution_spec"]
    assert execution_schema["properties"]["operation"]["enum"] == ["historical_rediscovery"]


def test_ollama_schema_restricts_kind_to_experiment_after_predictions():
    payload = {}

    def transport(request):
        payload.update(request)
        return {
            "message": {
                "content": json.dumps(
                    {
                        "kind": "experiment",
                        "target_ids": ["P1", "P2"],
                        "conditions": "Under bounded conditions.",
                        "objective": "Discriminate the predictions.",
                        "proposed_observation": "Observe the held-out position.",
                        "discrimination_basis": "The predictions disagree.",
                        "execution_spec": {"operation": "positional_presence", "position": 3.0},
                        "rationale": "A bounded experiment is required.",
                    }
                )
            }
        }

    context = DiscoveryContext(
        grounded_input_ids=(),
        findings=(),
        hypotheses=(),
        predictions=(
            {"id": "prediction-1"},
            {"id": "prediction-2"},
        ),
        experiments=(),
        actions_taken=(),
    )
    action = OllamaPlanner("qwen3:8b", transport=transport).choose(context)

    assert action.kind == "experiment"
    assert payload["format"]["properties"]["kind"]["enum"] == ["experiment"]


def test_ollama_prompt_makes_zero_hypothesis_transition_explicit():
    payload = {}

    def transport(request):
        payload.update(request)
        return {
            "message": {
                "content": json.dumps(
                    {
                        "kind": "hypothesis",
                        "target_ids": ["F1"],
                        "statement": "The missing observation reflects an unrepresented case.",
                        "rationale": "A GAP with no hypotheses requires an initial candidate explanation.",
                    }
                )
            }
        }

    gap_context = DiscoveryContext(
        grounded_input_ids=(),
        findings=({"id": "gap-1", "kind": "gap"},),
        hypotheses=(),
        predictions=(),
        experiments=(),
        actions_taken=(),
    )
    action = OllamaPlanner("qwen3:8b", transport=transport).choose(gap_context)

    assert action.kind == "hypothesis"
    system = payload["messages"][0]["content"]
    assert "ONLY valid candidate-generation action is hypothesis (or question)" in system
    assert "A GAP or TENSION is a finding, NOT a hypothesis" in system
    assert "Never propose prediction, experiment, request_evidence, or stop" in system


def test_ollama_schema_binds_target_ids_to_pending_discovery_stage():
    payload = {}

    def transport(request):
        payload.update(request)
        return {
            "message": {
                "content": json.dumps(
                    {
                        "kind": "hypothesis",
                        "target_ids": ["F1"],
                        "statement": "A candidate explanation.",
                        "rationale": "The pending gap requires another candidate.",
                    }
                )
            }
        }

    context = DiscoveryContext(
        grounded_input_ids=(),
        findings=(
            {"id": "gap-1", "kind": "gap"},
            {"id": "gap-2", "kind": "gap"},
        ),
        hypotheses=(
            {"id": "hypothesis-1", "finding_ids": ("gap-1",)},
        ),
        predictions=(),
        experiments=(),
        actions_taken=(),
    )
    action = OllamaPlanner("qwen3:8b", transport=transport).choose(context)

    assert action.kind == "hypothesis"
    assert payload["format"]["properties"]["target_ids"]["items"]["enum"] == ["F1", "F2"]
    assert "target_ids" in payload["format"]["required"]
    assert "statement" in payload["format"]["required"]


def test_ollama_historical_rediscovery_uses_distinct_numeric_forecasts_without_presence_flags():
    payload = {}

    def transport(request):
        payload.update(request)
        return {
            "message": {
                "content": json.dumps(
                    {
                        "kind": "prediction",
                        "target_ids": ["H1", "H2"],
                        "conditions": "bounded historical fixture",
                        "consequence": "the missing period has a quantitative property value",
                        "predicted_numeric_values": {"H1": 71.0, "H2": 74.0},
                        "rationale": "The competing hypotheses require distinct quantitative forecasts.",
                    }
                )
            }
        }

    context = DiscoveryContext(
        grounded_input_ids=(),
        findings=(),
        hypotheses=(
            {"id": "hypothesis-1"},
            {"id": "hypothesis-2"},
        ),
        predictions=(),
        experiments=(),
        actions_taken=(),
    )
    action = OllamaPlanner(
        "qwen3:8b",
        transport=transport,
        host_capabilities=("historical_rediscovery",),
    ).choose(context)

    assert action.predicted_numeric_values == {
        "hypothesis-1": 71.0,
        "hypothesis-2": 74.0,
    }
    assert action.expected_presences is None
    schema = payload["format"]
    assert "predicted_numeric_values" in schema["properties"]
    assert "expected_presences" not in schema["properties"]
    assert "predicted_numeric_values" in schema["required"]
    assert "expected_presences" not in schema["required"]


def test_ollama_blinded_rediscovery_context_uses_opaque_entities_and_one_property():
    payload = {}

    def transport(request):
        payload.update(request)
        return {
            "message": {
                "content": json.dumps(
                    {
                        "kind": "discover_gap",
                        "rationale": "The host-owned structural pass should identify the missing position.",
                    }
                )
            }
        }

    context = DiscoveryContext(
        grounded_input_ids=("observation-1",),
        findings=(),
        hypotheses=(),
        predictions=(),
        experiments=(),
        actions_taken=(),
        grounded_observations=(
            {
                "id": "observation-1",
                "kind": "observation",
                "payload": {
                    "label": "silicon",
                    "family": "group_14",
                    "period": 3,
                    "relative_atomic_mass": 28.085,
                    "density_g_cm3": 2.3296,
                },
                "created_at": "1885-12-31T00:00:00+00:00",
            },
        ),
    )
    OllamaPlanner(
        "qwen3:8b",
        transport=transport,
        host_capabilities=("historical_rediscovery",),
        rediscovery_property="relative_atomic_mass",
        blinded_rediscovery=True,
    ).choose(context)

    user_payload = payload["messages"][1]["content"]
    assert "silicon" not in user_payload.lower()
    assert '"entity": "E1"' in user_payload
    assert '"property_P": 28.085' in user_payload
    assert '"density_g_cm3"' not in user_payload


def test_ollama_receives_safe_host_evaluation_feedback_without_held_out_details():
    payload = {}

    def transport(request):
        payload.update(request)
        return {
            "message": {
                "content": json.dumps(
                    {
                        "kind": "stop",
                        "rationale": "The bounded experiment is complete and no evidence capability is available.",
                    }
                )
            }
        }

    context = DiscoveryContext(
        grounded_input_ids=(),
        findings=(),
        hypotheses=({"id": "hypothesis-1"},),
        predictions=({"id": "prediction-1"},),
        experiments=({"id": "experiment-1"},),
        actions_taken=(),
        evaluations=(
            {
                "id": "evaluation-secret",
                "result_id": "result-secret",
                "prediction_id": "prediction-1",
                "experiment_proposal_id": "experiment-secret",
                "outcome": "inconsistent",
                "observed_value": 938.25,
                "hidden_identity": "held_out_element",
            },
        ),
    )

    OllamaPlanner("qwen3:8b", transport=transport).choose(context)
    user_payload = payload["messages"][1]["content"]
    decoded = json.loads(user_payload)

    assert decoded["evaluation_feedback"] == [
        {
            "prediction": "P1",
            "verdict": "inconsistent",
            "rationale": (
                "The host evaluator marked this forecast inconsistent with the executed "
                "result under the registered evaluation rule."
            ),
        }
    ]
    assert "938.25" not in user_payload
    assert "held_out_element" not in user_payload
    assert "result-secret" not in user_payload
    assert "evaluation-secret" not in user_payload
    assert "experiment-secret" not in user_payload


def test_ollama_omits_evaluation_feedback_before_an_experiment():
    payload = {}

    def transport(request):
        payload.update(request)
        return {
            "message": {
                "content": json.dumps(
                    {
                        "kind": "stop",
                        "rationale": "The bounded exploration has no candidate finding.",
                    }
                )
            }
        }

    context = DiscoveryContext(
        grounded_input_ids=(),
        findings=(),
        hypotheses=(),
        predictions=(),
        experiments=(),
        actions_taken=(),
        evaluations=(
            {"prediction_id": "prediction-1", "outcome": "inconsistent"},
        ),
    )
    OllamaPlanner("qwen3:8b", transport=transport).choose(context)
    decoded = json.loads(payload["messages"][1]["content"])

    assert decoded["evaluation_feedback"] == []
