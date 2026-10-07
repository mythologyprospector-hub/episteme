"""Optional Ollama-backed planner for the bounded discovery driver.

This adapter keeps model-provider concerns outside Episteme's epistemic core.
The model can propose a bounded DiscoveryAction, but the core driver validates
and executes that action.
"""

from __future__ import annotations

import json
from typing import Any, Callable
from urllib.request import Request, urlopen

from .autonomy import DiscoveryAction, DiscoveryContext, PlannerActionError
from .evidence_request import resolve_evidence_capability


Transport = Callable[[dict[str, Any]], dict[str, Any]]


class OllamaPlanner:
    """Ask a local Ollama model for the next bounded discovery action."""

    def __init__(
        self,
        model: str,
        *,
        base_url: str = "http://127.0.0.1:11434",
        timeout: float = 120.0,
        transport: Transport | None = None,
        evidence_capabilities: tuple[str, ...] = (),
        host_capabilities: tuple[str, ...] = (),
    ) -> None:
        if not model.strip():
            raise ValueError("model must be non-empty")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._transport = transport
        self.evidence_capabilities = tuple(evidence_capabilities)
        self.host_capabilities = tuple(host_capabilities)

    def choose(self, context: DiscoveryContext) -> DiscoveryAction:
        payload = self._request_payload(context)
        response = self._transport(payload) if self._transport is not None else self._request(payload)
        content = response.get("message", {}).get("content")
        if not isinstance(content, str) or not content.strip():
            raise PlannerActionError("Ollama planner returned no message content")
        try:
            action_data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise PlannerActionError("Ollama planner returned invalid JSON") from exc
        if not isinstance(action_data, dict):
            raise PlannerActionError("Ollama planner JSON must be an object")
        try:
            return DiscoveryAction(**action_data)
        except (TypeError, ValueError) as exc:
            raise PlannerActionError(
                f"Ollama planner returned an invalid DiscoveryAction: {exc}; "
                f"response content={content!r}"
            ) from exc

    def _request_payload(self, context: DiscoveryContext) -> dict[str, Any]:
        context_data = {
            "grounded_input_ids": list(context.grounded_input_ids),
            "findings": list(context.findings),
            "exploration_observations": list(context.exploration_observations),
            "exploration_assessments": list(context.exploration_assessments),
            "available_host_capabilities": list(self.host_capabilities),
            "available_evidence_capabilities": list(self.evidence_capabilities),
            "available_evidence_capability_contracts": [
                {
                    "name": name,
                    "allowed_parameters": sorted(resolve_evidence_capability(name).allowed_parameters),
                    "supported_media_types": sorted(resolve_evidence_capability(name).supported_media_types),
                }
                for name in self.evidence_capabilities
            ],
            "hypotheses": list(context.hypotheses),
            "predictions": list(context.predictions),
            "experiments": list(context.experiments),
            "feedback": list(context.feedback),
            "actions_taken": [
                {
                    "kind": action.kind,
                    "target_ids": list(action.target_ids),
                    "statement": action.statement,
                    "consequence": action.consequence,
                    "consequences": list(action.consequences),
                    "conditions": action.conditions,
                    "objective": action.objective,
                    "proposed_observation": action.proposed_observation,
                    "discrimination_basis": action.discrimination_basis,
                    "execution_spec": dict(action.execution_spec) if action.execution_spec is not None else None,
                    "evidence_capability": action.evidence_capability,
                    "evidence_parameters": dict(action.evidence_parameters) if action.evidence_parameters is not None else None,
                    "requested_representation": action.requested_representation,
                    "rationale": action.rationale,
                }
                for action in context.actions_taken
            ],
        }
        system = (
            "You are the bounded planning component of a scientific inquiry instrument. "
            "Choose exactly one next action from: scout, assess_exploration, admit_exploration, discover_gap, question, "
            "hypothesis, prediction, experiment, request_evidence, stop. If the supplied context has no "
            "exploration observations and 'scout' is listed in available_host_capabilities, the first "
            "action MUST be scout. After a scout, if an exploration observation exists but "
            "has no assessment, choose assess_exploration for that observation. After an "
            "accepted assessment exists but the observation has not been admitted, choose "
            "admit_exploration for that observation. Do not stop merely because there are "
            "no GAP or TENSION findings while this exploration sequence is pending. "
            "You are not an authority over truth. Never claim that "
            "generated text is evidence. Use only identifiers present in the supplied "
            "context. For every target_ids field, COPY the exact id string from the matching context object; "
            "never invent, renumber, abbreviate, normalize, or infer an identifier such as HYPOTHESIS_002. "
            "In particular, prediction target_ids MUST be copied verbatim from the id fields in the supplied hypotheses list. "
            "Prefer a discriminating experiment when competing hypotheses exist. "
            "After a GAP or TENSION finding exists with no hypothesis, the ONLY valid candidate-generation action is hypothesis (or question). "
            "A GAP or TENSION is a finding, NOT a hypothesis. Never propose prediction, experiment, request_evidence, or stop while a candidate finding has zero hypotheses. "
            "After exactly one hypothesis exists for the finding, propose a distinct competing hypothesis for the same finding. "
            "After two or more "
            "competing hypotheses exist and have no predictions, propose discriminating "
            "predictions. After competing predictions exist with no experiment, the ONLY "
            "valid next action is experiment. If predictions exist and experiments is empty, "
            "NEVER choose request_evidence or stop; choose experiment. Once an experiment has been executed and its result and evaluations are present, request evidence when an explicitly available host capability could materially discriminate the active alternatives; otherwise choose stop. Do not propose another experiment for the same run. Do not stop merely because the GAP has been found; continue "
            "through candidate generation and discrimination until the bounded experiment has "
            "been executed or a justified evidence request/stop is reached. For kind='scout', request only a bounded host-owned scouting pass; you do not choose its grounded inputs, executor, limits, or configuration. For kind='assess_exploration', target exactly one supplied exploration observation id; the host decides acceptance, assessment method, provenance, and rationale. For kind='admit_exploration', target exactly one supplied exploration observation id; the host chooses the accepted assessment and admission policy. Never invent or supply assessment policy fields. For kind='discover_gap', request only the bounded host-owned structural discovery pass; you do not choose its grounded inputs, detector, limits, or configuration. For kind='request_evidence', choose only an explicitly available host evidence capability and obey its supplied capability contract. Use only allowed parameter names and one of its supported media types as requested_representation. The requested_representation value MUST be copied exactly from the capability's supported_media_types list; for the supplied crossref_works capability it MUST be exactly 'application/json'. Never omit requested_representation. A valid request_evidence action includes target_ids, evidence_capability, evidence_parameters, requested_representation, and rationale. Provide at least one existing motivation id and bounded evidence_parameters; never provide URLs, network instructions, provider credentials, or executable code. If external evidence is required and no host evidence capability is available, stop. "
            "Return one JSON object only. The JSON field for the action type is named "
            "'kind', never 'action'. The field 'rationale' is REQUIRED on EVERY action, "
            "including prediction, and must be a non-empty string explaining why that action "
            "is the correct next bounded step. Never omit rationale. For example, a prediction "
            "must include kind, target_ids, conditions, consequence or consequences, and "
            "rationale. The only allowed JSON fields are: kind, target_ids, "
            "statement, consequence, consequences, conditions, objective, "
            "proposed_observation, discrimination_basis, expected_presences, execution_spec, evidence_capability, "
            "evidence_parameters, requested_representation, rationale. Do not invent other field names. A hypothesis action creates a NEW hypothesis about a finding. "
            "For kind='question' or kind='hypothesis', target_ids MUST contain exactly "
            "one existing GAP or TENSION finding id. NEVER put an existing hypothesis id "
            "in target_ids for a hypothesis action. For kind='hypothesis', statement is "
            "MANDATORY and must be a non-empty string stating the candidate explanation. "
            "If you cannot provide that statement, choose kind='question' instead. "
            "Example: if the finding id is GAP_001, "
            "a new hypothesis must use target_ids=[\"GAP_001\"] and MUST also include a non-empty "
            "statement, for example {\"kind\":\"hypothesis\",\"target_ids\":[\"GAP_001\"],\"statement\":\"Candidate explanation\",\"rationale\":\"This creates the first testable candidate for the finding.\"}. "
            "For kind='prediction', target_ids MUST contain at least two existing "
            "hypothesis ids, because a prediction compares hypotheses. For prediction, conditions MUST be a plain JSON string, never an object or array; "
            "expected_presences MUST be an object mapping each target hypothesis id to a boolean; "
            "consequence, when used, MUST be a string; consequences, when used, MUST be an array of strings. "
            "Do not emit uncertainty or any other field not listed above. "
            "For kind='experiment', target_ids MUST contain at least two existing "
            "prediction ids and conditions, objective, proposed_observation, "
            "discrimination_basis, and execution_spec are required. execution_spec "
            "must contain only operation='positional_presence', numeric position, and optional position_key. "
            "Do not add any other execution_spec fields; the host supplies experiment inputs and prediction expectations. "
            "Do not name a Python callable, command, URL, or evaluator. For kind='stop', rationale is required. "
            "Always include rationale. If feedback is supplied, it describes a rejected prior action; correct the action instead of repeating the same error."
        )
        return {
            "model": self.model,
            "stream": False,
            "format": {
                "type": "object",
                "properties": {
                    "kind": {
                        "type": "string",
                        "enum": ["scout", "assess_exploration", "admit_exploration", "discover_gap", "question", "hypothesis", "prediction", "experiment", "request_evidence", "stop"],
                    },
                    "target_ids": {"type": "array", "items": {"type": "string"}},
                    "statement": {"type": "string"},
                    "consequence": {"type": "string"},
                    "consequences": {"type": "array", "items": {"type": "string"}},
                    "conditions": {"type": "string"},
                    "expected_presences": {
                        "type": "object",
                        "additionalProperties": {"type": "boolean"},
                    },
                    "objective": {"type": "string"},
                    "proposed_observation": {"type": "string"},
                    "discrimination_basis": {"type": "string"},
                    "evidence_capability": {"type": "string"},
                    "evidence_parameters": {"type": "object"},
                    "requested_representation": {"type": "string"},
                    "execution_spec": {
                        "type": "object",
                        "properties": {
                            "operation": {"type": "string", "enum": ["positional_presence"]},
                            "position": {"type": "number"},
                            "position_key": {"type": "string"},
                        },
                        "required": ["operation", "position"],
                        "additionalProperties": False,
                    },
                    "rationale": {"type": "string"},
                },
                "required": ["kind", "rationale"],
                "additionalProperties": False,
                "oneOf": [
                    {
                        "properties": {"kind": {"const": "scout"}},
                        "required": ["kind", "rationale"],
                    },
                    {
                        "properties": {"kind": {"const": "assess_exploration"}},
                        "required": ["kind", "target_ids", "rationale"],
                    },
                    {
                        "properties": {"kind": {"const": "admit_exploration"}},
                        "required": ["kind", "target_ids", "rationale"],
                    },
                    {
                        "properties": {"kind": {"const": "discover_gap"}},
                        "required": ["kind", "rationale"],
                    },
                    {
                        "properties": {"kind": {"const": "question"}},
                        "required": ["kind", "target_ids", "rationale"],
                    },
                    {
                        "properties": {"kind": {"const": "hypothesis"}},
                        "required": ["kind", "target_ids", "statement", "rationale"],
                    },
                    {
                        "properties": {"kind": {"const": "prediction"}},
                        "required": ["kind", "target_ids", "conditions", "expected_presences", "rationale"],
                        "oneOf": [
                            {"required": ["consequence"]},
                            {"required": ["consequences"]},
                        ],
                    },
                    {
                        "properties": {"kind": {"const": "experiment"}},
                        "required": [
                            "kind",
                            "target_ids",
                            "conditions",
                            "objective",
                            "proposed_observation",
                            "discrimination_basis",
                            "execution_spec",
                            "rationale",
                        ],
                    },
                    {
                        "properties": {"kind": {"const": "request_evidence"}},
                        "required": [
                            "kind",
                            "target_ids",
                            "evidence_capability",
                            "evidence_parameters",
                            "requested_representation",
                            "rationale",
                        ],
                    },
                    {
                        "properties": {"kind": {"const": "stop"}},
                        "required": ["kind", "rationale"],
                    },
                ],
            },
            "messages": [
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": json.dumps(context_data, sort_keys=True),
                },
            ],
        }

    def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = Request(
            self.base_url + "/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=self.timeout) as response:
            body = response.read().decode("utf-8")
        result = json.loads(body)
        if not isinstance(result, dict):
            raise ValueError("Ollama response must be a JSON object")
        return result
