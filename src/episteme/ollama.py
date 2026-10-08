"""Optional Ollama-backed planner for the bounded discovery driver.

This adapter keeps model-provider concerns outside Episteme's epistemic core.
The model can propose a bounded DiscoveryAction, but the core driver validates
and executes that action.
"""

from __future__ import annotations

import json
from typing import Mapping, Any, Callable
from urllib.request import Request, urlopen

from .autonomy import DiscoveryAction, DiscoveryContext, PlannerActionError
from .evidence_request import resolve_evidence_capability


Transport = Callable[[dict[str, Any]], dict[str, Any]]


def _planner_id_aliases(context: DiscoveryContext) -> tuple[dict[str, str], dict[str, str]]:
    """Map opaque store ids to short, model-safe handles for one planning turn."""
    groups = (
        (context.grounded_observations, "O"),
        (context.findings, "F"),
        (context.exploration_observations, "E"),
        (context.exploration_assessments, "A"),
        (context.hypotheses, "H"),
        (context.predictions, "P"),
        (context.experiments, "X"),
    )
    aliases: dict[str, str] = {}
    for items, prefix in groups:
        for index, item in enumerate(items, start=1):
            item_id = item.get("id")
            if isinstance(item_id, str):
                aliases[item_id] = f"{prefix}{index}"
    for index, item_id in enumerate(context.grounded_input_ids, start=1):
        if isinstance(item_id, str):
            aliases.setdefault(item_id, f"O{index}")
    return aliases, {handle: item_id for item_id, handle in aliases.items()}


def _alias_value(value: Any, aliases: dict[str, str]) -> Any:
    if isinstance(value, str):
        return aliases.get(value, value)
    if isinstance(value, Mapping):
        return {
            aliases.get(key, key) if isinstance(key, str) else key: _alias_value(item, aliases)
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        return tuple(_alias_value(item, aliases) for item in value)
    if isinstance(value, list):
        return [_alias_value(item, aliases) for item in value]
    return value


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
        _, handle_to_id = _planner_id_aliases(context)
        if "target_ids" in action_data:
            values = action_data["target_ids"]
            if not isinstance(values, list):
                raise PlannerActionError("target_ids must be an array of planner handles")
            if len(values) != len(set(values)):
                raise PlannerActionError("target_ids contains duplicate planner handles")
            try:
                action_data["target_ids"] = [handle_to_id[value] for value in values]
            except (KeyError, TypeError) as exc:
                raise PlannerActionError("target_ids must contain only supplied planner handles") from exc
        if "expected_presences" in action_data:
            expected = action_data["expected_presences"]
            if not isinstance(expected, dict):
                raise PlannerActionError("expected_presences must be an object")
            try:
                action_data["expected_presences"] = {handle_to_id[key]: value for key, value in expected.items()}
            except (KeyError, TypeError) as exc:
                raise PlannerActionError("expected_presences must use supplied planner handles") from exc
        try:
            return DiscoveryAction(**action_data)
        except (TypeError, ValueError) as exc:
            raise PlannerActionError(
                f"Ollama planner returned an invalid DiscoveryAction: {exc}; "
                f"response content={content!r}"
            ) from exc

    def _request_payload(self, context: DiscoveryContext) -> dict[str, Any]:
        aliases, _ = _planner_id_aliases(context)
        context_data = {
            "grounded_input_ids": _alias_value(list(context.grounded_input_ids), aliases),
            "grounded_observations": _alias_value(list(context.grounded_observations), aliases),
            "findings": _alias_value(list(context.findings), aliases),
            "exploration_observations": _alias_value(list(context.exploration_observations), aliases),
            "exploration_assessments": _alias_value(list(context.exploration_assessments), aliases),
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
            "hypotheses": _alias_value(list(context.hypotheses), aliases),
            "predictions": _alias_value(list(context.predictions), aliases),
            "experiments": _alias_value(list(context.experiments), aliases),
            "feedback": list(context.feedback),
            "actions_taken": [
                {
                    "kind": action.kind,
                    "target_ids": _alias_value(list(action.target_ids), aliases),
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
        context_target_ids = tuple(
            dict.fromkeys(
                item["id"]
                for items in (
                    context.findings,
                    context.exploration_observations,
                    context.exploration_assessments,
                    context.hypotheses,
                    context.predictions,
                    context.experiments,
                )
                for item in items
                if isinstance(item.get("id"), str)
            )
        )
        target_id_candidates = context_target_ids
        candidate_findings = tuple(
            item
            for item in context.findings
            if item.get("kind") in {"gap", "tension"}
        )
        hypothesis_counts = {
            finding.get("id"): sum(
                finding.get("id") in hypothesis.get("finding_ids", ())
                for hypothesis in context.hypotheses
            )
            for finding in candidate_findings
        }
        pending_findings = tuple(
            finding_id
            for finding_id, count in hypothesis_counts.items()
            if count < 2
        )
        if pending_findings:
            target_id_candidates = pending_findings
        elif len(context.hypotheses) >= 2 and not context.predictions:
            target_id_candidates = tuple(
                item.get("id")
                for item in context.hypotheses
                if isinstance(item.get("id"), str)
            )
        elif context.predictions and not context.experiments:
            target_id_candidates = tuple(
                item.get("id")
                for item in context.predictions
                if isinstance(item.get("id"), str)
            )

        target_ids_schema: dict[str, Any] = {"type": "array", "items": {"type": "string"}}
        if target_id_candidates:
            target_ids_schema["items"] = {
                "type": "string",
                "enum": [aliases[item_id] for item_id in target_id_candidates],
            }
        if len(context.hypotheses) >= 2 and not context.predictions:
            target_ids_schema.update({"minItems": 2, "maxItems": 2, "uniqueItems": True})

        system = (
            "You are the bounded planning component of a scientific inquiry instrument. "
            "Choose exactly one next action from: scout, assess_exploration, admit_exploration, discover_gap, question, "
            "hypothesis, prediction, experiment, request_evidence, stop. If the supplied context has no "
            "exploration observations and 'scout' is listed in available_host_capabilities, the first "
            "action MUST be scout. After a scout, if an exploration observation exists but "
            "has no assessment, choose assess_exploration for that observation. After an "
            "accepted assessment exists but the observation has not been admitted, choose "
            "admit_exploration for that observation. After an accepted exploration "
            "observation has been admitted, the next action MUST be discover_gap when that "
            "host capability is available; do not stop merely because there are no GAP or "
            "TENSION findings. Do not stop merely because there are no GAP or TENSION "
            "findings while this exploration sequence is pending. "
            "For quantitative reasoning, use the supplied grounded_observations payloads. These are host-selected discovery inputs and may be used for calculations. Never assume or infer any held-out observation that is not present there. "            "If 'historical_rediscovery' is listed in available_host_capabilities, make the quantitative forecast from the supplied observations only, include predicted_numeric_value on every quantitative prediction, and use execution_spec.operation='historical_rediscovery' for the bounded held-out test. Do not put the held-out observation into your reasoning unless it is supplied in grounded_observations. "            "You are not an authority over truth. Never claim that "
            "generated text is evidence. Use only identifiers present in the supplied "
            "context. For every target_ids field, COPY the exact id string from the matching context object; "
            "never invent, renumber, abbreviate, normalize, or infer an identifier such as HYPOTHESIS_002. "
            "In particular, prediction target_ids MUST use the short planner handles shown in the supplied context; never emit the underlying opaque ids. "
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
            "been executed or a justified evidence request/stop is reached. For kind='scout', request only a bounded host-owned scouting pass; you do not choose its grounded inputs, executor, limits, or configuration. For kind='assess_exploration', target exactly one supplied exploration observation id; the host decides acceptance, assessment method, provenance, and rationale. For kind='admit_exploration', target exactly one supplied exploration observation id; the host chooses the accepted assessment and admission policy. Never invent or supply assessment policy fields. For kind='discover_gap', request only the bounded host-owned structural discovery pass; you do not choose its grounded inputs, detector, limits, or configuration. For kind='request_evidence', choose only an explicitly available host evidence capability and obey its supplied capability contract. Use only allowed parameter names and one of its supported media types as requested_representation. For crossref_works, the ONLY allowed parameter names are 'rows' and 'query.title'; NEVER use 'query' or any other name. The requested_representation value MUST be copied exactly from the capability's supported_media_types list; for the supplied crossref_works capability it MUST be exactly 'application/json'. Never omit requested_representation. A valid request_evidence action includes target_ids, evidence_capability, evidence_parameters, requested_representation, and rationale. Provide at least one existing motivation id and bounded evidence_parameters; never provide URLs, network instructions, provider credentials, or executable code. If external evidence is required and no host evidence capability is available, stop. "
            "IMPORTANT: The structured output schema requires a rationale for every action. The scout action is especially prone to being returned as only {\"kind\":\"scout\"}; that is INVALID. A valid scout response MUST contain both fields, exactly like {\"kind\":\"scout\",\"rationale\":\"Begin the bounded host-owned scouting pass.\"}. "
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
            "prediction MUST include consequence as a non-empty string. Use the singular consequence field; do not use the consequences array. For quantitative predictions, include predicted_numeric_value as the machine-checkable numeric forecast. "
            "Do not emit uncertainty or any other field not listed above. "
            "For kind='experiment', target_ids MUST contain at least two existing "
            "prediction ids and conditions, objective, proposed_observation, The experiment target_ids MUST be copied from the predictions list, never from hypotheses, findings, or experiments; when two predictions exist, copy both prediction id strings verbatim. "
            "discrimination_basis, and execution_spec are required. For a historical "
            "rediscovery capability, execution_spec must contain only "
            "operation='historical_rediscovery'; for positional_presence it must contain "
            "operation='positional_presence' and numeric position. Do not add any other "
            "execution_spec fields; the host supplies experiment inputs and prediction "
            "expectations. "
            "Do not name a Python callable, command, URL, or evaluator. For kind='stop', rationale is required. "
            "Always include rationale. If feedback is supplied, it describes a rejected prior action; correct the action instead of repeating the same error."
        )
        required_fields = ["kind", "rationale"]
        if len(context.hypotheses) >= 2 and not context.predictions:
            required_fields.extend(["target_ids", "conditions", "consequence", "expected_presences"])
        if context.predictions and not context.experiments:
            required_fields.extend(
                [
                    "target_ids",
                    "conditions",
                    "objective",
                    "proposed_observation",
                    "discrimination_basis",
                    "execution_spec",
                ]
            )

        allowed_kinds = [
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
        if context.predictions and not context.experiments:
            allowed_kinds = ["experiment"]
        elif not candidate_findings:
            # Match the core validation boundary in the structured schema so a
            # model cannot spend its retry budget proposing candidate actions
            # before the host-owned structural discovery pass has produced a
            # GAP or TENSION finding.
            allowed_kinds = ["discover_gap"]
        elif pending_findings:
            finding_id = pending_findings[0]
            count = hypothesis_counts[finding_id]
            allowed_kinds = ["hypothesis", "question"] if count == 0 else ["hypothesis"]

        return {
            "model": self.model,
            "stream": False,
            "format": {
                "type": "object",
                "properties": {
                    "kind": {
                        "type": "string",
                        "enum": allowed_kinds,
                    },
                    "target_ids": target_ids_schema,
                    "statement": {"type": "string"},
                    "consequence": {"type": "string"},
                    "consequences": {"type": "array", "items": {"type": "string"}},
                    "conditions": {"type": "string"},
                    "expected_presences": (
                        {
                            "type": "object",
                            "properties": {aliases[item["id"]]: {"type": "boolean"} for item in context.hypotheses if isinstance(item.get("id"), str)},
                            "required": [aliases[item["id"]] for item in context.hypotheses if isinstance(item.get("id"), str)],
                            "additionalProperties": False,
                        }
                        if context.hypotheses
                        else {"type": "object", "additionalProperties": {"type": "boolean"}}
                    ),
                    "objective": {"type": "string"},
                    "proposed_observation": {"type": "string"},
                    "discrimination_basis": {"type": "string"},
                    "evidence_capability": {"type": "string"},
                    "evidence_parameters": {
                        "type": "object",
                        "properties": {
                            "rows": {"type": "integer", "minimum": 1, "maximum": 1000},
                            "query.title": {"type": "string", "minLength": 1},
                        },
                        "additionalProperties": False,
                    },
                    "requested_representation": {"type": "string"},
                    "predicted_numeric_value": {"type": "number"},
                    "execution_spec": {
                        "type": "object",
                        "properties": {
                            "operation": {"type": "string", "enum": ["positional_presence", "historical_rediscovery"]},
                            "position": {"type": "number"},
                        },
                        "required": ["operation"],
                        "additionalProperties": False,
                    },
                    "rationale": {"type": "string", "minLength": 1},
                },
                "required": required_fields,
                "additionalProperties": False,
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
