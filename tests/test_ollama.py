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


def test_historical_rediscovery_rejects_hypothesis_without_quantitative_rule():
    content = json.dumps(
        {
            "kind": "hypothesis",
            "target_ids": ["F1"],
            "statement": "The missing value follows a midpoint relationship.",
            "rationale": "A testable quantitative hypothesis is required.",
        }
    )
    context = DiscoveryContext(
        grounded_input_ids=(),
        findings=({"id": "gap-1", "kind": "gap"},),
        hypotheses=(),
        predictions=(),
        experiments=(),
        actions_taken=(),
    )
    planner = OllamaPlanner(
        "qwen3:14b",
        transport=lambda _payload: {"message": {"content": content}},
        host_capabilities=("historical_rediscovery",),
    )

    with pytest.raises(
        PlannerActionError,
        match="historical rediscovery hypothesis requires a quantitative_rule object",
    ):
        planner.choose(context)


def test_historical_rediscovery_preserves_required_quantitative_rule():
    payload = {}
    content = json.dumps(
        {
            "kind": "hypothesis",
            "target_ids": ["F1"],
            "statement": "The missing value is the midpoint of positions 3 and 5.",
            "quantitative_rule": {
                "operation": "midpoint",
                "property": "relative_atomic_mass",
                "input_positions": [3, 5],
            },
            "rationale": "This rule can be computed from supplied observations.",
        }
    )
    context = DiscoveryContext(
        grounded_input_ids=(),
        findings=({"id": "gap-1", "kind": "gap"},),
        hypotheses=(),
        predictions=(),
        experiments=(),
        actions_taken=(),
        grounded_observations=(
            {"id": "observation-3", "kind": "observation", "payload": {"period": 3, "relative_atomic_mass": 28.085}},
            {"id": "observation-5", "kind": "observation", "payload": {"period": 5, "relative_atomic_mass": 118.710}},
        ),
    )

    def transport(request):
        payload.update(request)
        return {"message": {"content": content}}

    action = OllamaPlanner(
        "qwen3:14b",
        transport=transport,
        host_capabilities=("historical_rediscovery",),
    ).choose(context)

    assert action.quantitative_rule == {
        "operation": "midpoint",
        "property": "relative_atomic_mass",
        "input_positions": [3, 5],
    }
    assert "quantitative_rule" in payload["format"]["required"]
    rule_schema = payload["format"]["properties"]["quantitative_rule"]["properties"]
    assert rule_schema["operation"]["enum"] == [
        "midpoint", "average", "geometric_mean",
        "addition_with_previous_interval", "subtract_difference",
        "difference_subtraction", "linear_regression",
        "linear_extrapolation", "exponential_regression",
    ]
    assert rule_schema["property"]["enum"] == ["relative_atomic_mass"]
    assert rule_schema["input_positions"]["items"]["enum"] == [3.0, 5.0]



def test_historical_rediscovery_prompt_forbids_repeating_competing_rules():
    payload = {}

    def transport(request):
        payload.update(request)
        return {
            "message": {
                "content": json.dumps({
                    "kind": "stop",
                    "rationale": "The bounded test cannot continue.",
                })
            }
        }

    OllamaPlanner(
        "qwen:14b",
        transport=transport,
        host_capabilities=("historical_rediscovery",),
    ).choose(_context())

    system_prompt = payload["messages"][0]["content"]
    assert "inspect every existing hypothesis and its quantitative_rule" in system_prompt
    assert "Never reuse an existing rule with the same operation, property, and input_positions" in system_prompt
    assert "a rejected duplicate must be corrected, not repeated" in system_prompt
    assert "Rule arity is strict" in system_prompt
    assert "`average` may use two or more input positions" in system_prompt
    assert "every other supported operation" in system_prompt
    assert "Never submit extra positions to a two-input operation" in system_prompt
    assert "statement, quantitative_rule, consequence" in system_prompt


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
    assert schema["properties"]["execution_spec"]["properties"]["position"]["type"] == "number"
    assert schema["properties"]["execution_spec"]["required"] == ["operation", "position"]



def test_ollama_blinded_rule_candidates_use_host_side_periods():
    payload = {}

    def transport(request):
        payload.update(request)
        return {"message": {"content": json.dumps({
            "kind": "hypothesis",
            "target_ids": ["F1"],
            "statement": "A distinct rule relates supplied observations.",
            "quantitative_rule": {
                "operation": "geometric_mean",
                "property": "property_P",
                "input_positions": [2.0, 5.0],
            },
            "rationale": "Use an executable relationship from the supplied observations.",
        })}}

    # The host context intentionally keeps the original payload; only the
    # model-facing context is transformed to blinded position/property aliases.
    context = DiscoveryContext(
        grounded_input_ids=("observation-2", "observation-3", "observation-5"),
        grounded_observations=(
            {"id": "observation-2", "payload": {"period": 2.0, "relative_atomic_mass": 10.0}},
            {"id": "observation-3", "payload": {"period": 3.0, "relative_atomic_mass": 20.0}},
            {"id": "observation-5", "payload": {"period": 5.0, "relative_atomic_mass": 40.0}},
        ),
        findings=({"id": "gap-1", "kind": "gap"},),
        hypotheses=(),
        predictions=(),
        experiments=(),
        actions_taken=(),
    )
    action = OllamaPlanner(
        "qwen:14b",
        transport=transport,
        host_capabilities=("historical_rediscovery",),
        blinded_rediscovery=True,
    ).choose(context)

    assert action.kind == "hypothesis"
    assert {
        "operation": "geometric_mean",
        "property": "property_P",
        "input_positions": [2.0, 5.0],
    } in payload["format"]["properties"]["quantitative_rule"]["enum"]
    user_payload = payload["messages"][1]["content"]
    assert '"position": 2.0' in user_payload
    assert '"period"' not in user_payload
    assert "relative_atomic_mass" not in user_payload


def test_ollama_historical_hypothesis_schema_excludes_existing_quantitative_rule():
    payload = {}

    def transport(request):
        payload.update(request)
        return {"message": {"content": json.dumps({
            "kind": "hypothesis",
            "target_ids": ["F1"],
            "statement": "A distinct rule relates the supplied observations.",
            "quantitative_rule": {
                "operation": "geometric_mean",
                "property": "property_P",
                "input_positions": [2.0, 5.0],
            },
            "rationale": "Offer a distinct executable candidate.",
        })}}

    context = DiscoveryContext(
        grounded_input_ids=("observation-2", "observation-3", "observation-5"),
        grounded_observations=(
            {"id": "observation-2", "payload": {"position": 2.0, "period": 2.0, "value": 10.0}},
            {"id": "observation-3", "payload": {"position": 3.0, "period": 3.0, "value": 20.0}},
            {"id": "observation-5", "payload": {"position": 5.0, "period": 5.0, "value": 40.0}},
        ),
        findings=({"id": "gap-1", "kind": "gap"},),
        hypotheses=({
            "id": "hypothesis-1",
            "finding_ids": ("gap-1",),
            "quantitative_rule": {
                "operation": "midpoint",
                "property": "property_P",
                "input_positions": [3.0, 5.0],
            },
        },),
        predictions=(),
        experiments=(),
        actions_taken=(),
    )
    action = OllamaPlanner(
        "qwen:14b",
        transport=transport,
        host_capabilities=("historical_rediscovery",),
        blinded_rediscovery=True,
    ).choose(context)

    assert action.kind == "hypothesis"
    allowed_rules = payload["format"]["properties"]["quantitative_rule"]["enum"]
    assert {
        "operation": "midpoint", "property": "property_P", "input_positions": [3.0, 5.0]
    } not in allowed_rules
    assert {
        "operation": "geometric_mean", "property": "property_P", "input_positions": [2.0, 5.0]
    } in allowed_rules


def test_ollama_historical_hypothesis_fails_closed_when_no_distinct_rule_exists():
    operations = (
        "midpoint", "average", "geometric_mean",
        "addition_with_previous_interval", "subtract_difference",
        "difference_subtraction", "linear_regression",
        "linear_extrapolation", "exponential_regression",
    )
    hypotheses = tuple({
        "id": f"hypothesis-{index}",
        "finding_ids": ("gap-1",) if index == 0 else (),
        "quantitative_rule": {
            "operation": operation, "property": "property_P", "input_positions": [3.0, 5.0]
        },
    } for index, operation in enumerate(operations))
    context = DiscoveryContext(
        grounded_input_ids=("observation-3", "observation-5"),
        grounded_observations=(
            {"id": "observation-3", "payload": {"position": 3.0, "period": 3.0, "value": 20.0}},
            {"id": "observation-5", "payload": {"position": 5.0, "period": 5.0, "value": 40.0}},
        ),
        findings=({"id": "gap-1", "kind": "gap"},),
        hypotheses=hypotheses,
        predictions=(),
        experiments=(),
        actions_taken=(),
    )
    planner = OllamaPlanner(
        "qwen:14b",
        transport=lambda _request: pytest.fail("model must not be asked to invent a rule"),
        host_capabilities=("historical_rediscovery",),
        blinded_rediscovery=True,
    )
    with pytest.raises(PlannerActionError, match="no distinct executable quantitative rule"):
        planner.choose(context)


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
    assert "position" not in execution_schema["properties"]
    assert execution_schema["required"] == ["operation"]


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


def test_ollama_historical_rediscovery_prompt_requires_unrounded_numeric_forecasts():
    payload = {}

    def transport(request):
        payload.update(request)
        return {
            "message": {
                "content": json.dumps({
                    "kind": "stop",
                    "rationale": "The bounded process has no further available actions.",
                })
            }
        }

    context = DiscoveryContext(
        grounded_input_ids=(),
        findings=(),
        hypotheses=(),
        predictions=(),
        experiments=({"id": "experiment-1"},),
        actions_taken=(),
    )
    OllamaPlanner(
        "qwen3:8b",
        transport=transport,
        host_capabilities=("historical_rediscovery",),
    ).choose(context)

    system = payload["messages"][0]["content"]
    assert "Do not round intermediate calculations or numeric forecasts" in system
    assert "preserve the full precision implied by the supplied values and rule" in system


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
    assert '"historical_rediscovery_property": "property_P"' in user_payload
    rule_schema = payload["format"]["properties"]["quantitative_rule"]["properties"]
    assert rule_schema["property"]["enum"] == ["property_P"]


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
            "forecast": None,
            "compared_hypotheses": [],
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


def test_ollama_passes_safe_inconclusive_evaluation_feedback():
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
                "outcome": "inconclusive",
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
            "forecast": None,
            "compared_hypotheses": [],
            "verdict": "inconclusive",
            "rationale": (
                "The host evaluator could not conclusively evaluate this forecast "
                "under the registered evaluation rule."
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


def test_ollama_evaluation_feedback_links_each_verdict_to_its_forecast_and_hypotheses():
    payload = {}

    def transport(request):
        payload.update(request)
        return {
            "message": {
                "content": json.dumps({
                    "kind": "stop",
                    "rationale": "The bounded experiment is complete.",
                })
            }
        }

    context = DiscoveryContext(
        grounded_input_ids=(),
        findings=(),
        hypotheses=(
            {"id": "hypothesis-1", "statement": "First candidate."},
            {"id": "hypothesis-2", "statement": "Second candidate."},
        ),
        predictions=(
            {
                "id": "prediction-1",
                "predicted_numeric_value": 44.16,
                "comparison_hypothesis_ids": ("hypothesis-1", "hypothesis-2"),
            },
            {
                "id": "prediction-2",
                "predicted_numeric_value": 73.3975,
                "comparison_hypothesis_ids": ("hypothesis-1", "hypothesis-2"),
            },
        ),
        experiments=({"id": "experiment-1"},),
        actions_taken=(),
        evaluations=(
            {"prediction_id": "prediction-1", "outcome": "inconsistent"},
            {"prediction_id": "prediction-2", "outcome": "consistent"},
        ),
    )

    OllamaPlanner("qwen3:8b", transport=transport).choose(context)
    decoded = json.loads(payload["messages"][1]["content"])

    assert decoded["evaluation_feedback"] == [
        {
            "prediction": "P1",
            "forecast": 44.16,
            "compared_hypotheses": ["H1", "H2"],
            "verdict": "inconsistent",
            "rationale": (
                "The host evaluator marked this forecast inconsistent with the executed "
                "result under the registered evaluation rule."
            ),
        },
        {
            "prediction": "P2",
            "forecast": 73.3975,
            "compared_hypotheses": ["H1", "H2"],
            "verdict": "consistent",
            "rationale": (
                "The host evaluator marked this forecast consistent with the executed "
                "result under the registered evaluation rule."
            ),
        },
    ]



@pytest.mark.parametrize(
    ("operation", "property_name", "positions", "message"),
    [
        ("gap_fill", "relative_atomic_mass", [3, 5], "supported operation"),
        ("midpoint", "density_g_cm3", [3, 5], "property must match"),
        ("midpoint", "relative_atomic_mass", [3, 9], "input_positions must come"),
    ],
)
def test_historical_rediscovery_rejects_unverifiable_quantitative_rules(
    operation, property_name, positions, message
):
    content = json.dumps({
        "kind": "hypothesis",
        "target_ids": ["F1"],
        "statement": "A numeric rule predicts the missing property.",
        "quantitative_rule": {
            "operation": operation,
            "property": property_name,
            "input_positions": positions,
        },
        "rationale": "The proposed relationship should be independently computable.",
    })
    context = DiscoveryContext(
        grounded_input_ids=("observation-3", "observation-5"),
        findings=({"id": "gap-1", "kind": "gap"},),
        hypotheses=(),
        predictions=(),
        experiments=(),
        actions_taken=(),
        grounded_observations=(
            {"id": "observation-3", "kind": "observation", "payload": {"period": 3, "relative_atomic_mass": 28.085}},
            {"id": "observation-5", "kind": "observation", "payload": {"period": 5, "relative_atomic_mass": 118.710}},
        ),
    )
    planner = OllamaPlanner(
        "qwen3:14b",
        transport=lambda _payload: {"message": {"content": content}},
        host_capabilities=("historical_rediscovery",),
    )
    with pytest.raises(PlannerActionError, match=message):
        planner.choose(context)



def test_ollama_receives_structured_host_rejection_feedback_for_retry():
    payload = {}
    rejection = (
        "The previous proposed action was rejected: competing hypotheses must use distinct "
        "quantitative rules. Choose a corrected action. Rejected action details (JSON): "
        '{"kind":"hypothesis","target_ids":["opaque-finding-id"],'
        '"quantitative_rule":{"operation":"geometric_mean","property":"property_P",'
        '"input_positions":[3,5]},"predicted_numeric_values":null}. '
        "Correct the specific rejected fields; do not repeat the same proposal."
    )

    def transport(request):
        payload.update(request)
        return {
            "message": {
                "content": json.dumps({
                    "kind": "stop",
                    "rationale": "This fixture only verifies retry-feedback transport.",
                })
            }
        }

    context = DiscoveryContext(
        grounded_input_ids=(),
        findings=({"id": "opaque-finding-id", "kind": "gap"},),
        hypotheses=({"id": "hypothesis-1", "finding_ids": ("opaque-finding-id",)},),
        predictions=(),
        experiments=(),
        actions_taken=(),
        feedback=(rejection,),
        rejected_actions=(
            {
                "kind": "hypothesis",
                "target_ids": ["opaque-finding-id"],
                "quantitative_rule": {
                    "operation": "geometric_mean",
                    "property": "property_P",
                    "input_positions": [3, 5],
                },
                "predicted_numeric_values": None,
            },
        ),
    )

    OllamaPlanner("qwen3:8b", transport=transport).choose(context)
    user_payload = payload["messages"][1]["content"]
    decoded = json.loads(user_payload)

    assert decoded["feedback"] == [rejection]
    assert "competing hypotheses must use distinct quantitative rules" in user_payload
    assert '"operation":"geometric_mean"' in decoded["feedback"][0]
    assert '"input_positions":[3,5]' in decoded["feedback"][0]
    assert decoded["rejected_actions"] == [
        {
            "kind": "hypothesis",
            "target_ids": ["F1"],
            "quantitative_rule": {
                "operation": "geometric_mean",
                "property": "property_P",
                "input_positions": [3, 5],
            },
            "predicted_numeric_values": None,
        }
    ]
    assert "opaque-finding-id" not in json.dumps(decoded["rejected_actions"])

def test_ollama_rejected_numeric_forecasts_use_model_handles():
    payload = {}

    def transport(request):
        payload.update(request)
        return {"message": {"content": json.dumps({
            "kind": "prediction",
            "target_ids": ["H1", "H2"],
            "conditions": "bounded historical fixture",
            "consequence": "the competing rules produce distinct forecasts",
            "predicted_numeric_values": {"H1": 37.7, "H2": 4.8},
            "rationale": "Revise the rejected forecasts using the supplied rule evidence.",
        })}}

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
        rejected_actions=(
            {
                "kind": "prediction",
                "target_ids": ("hypothesis-1", "hypothesis-2"),
                "predicted_numeric_values": {
                    "hypothesis-1": 0.6,
                    "hypothesis-2": 0.9,
                },
            },
        ),
    )

    OllamaPlanner(
        "qwen:14b",
        transport=transport,
        host_capabilities=("historical_rediscovery",),
    ).choose(context)

    decoded = json.loads(payload["messages"][1]["content"])
    assert decoded["rejected_actions"] == [
        {
            "kind": "prediction",
            "target_ids": ["H1", "H2"],
            "quantitative_rule": None,
            "predicted_numeric_values": {"H1": 0.6, "H2": 0.9},
        }
    ]
    assert "hypothesis-1" not in payload["messages"][1]["content"]
    assert "hypothesis-2" not in payload["messages"][1]["content"]

