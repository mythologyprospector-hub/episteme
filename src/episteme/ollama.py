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
    ) -> None:
        if not model.strip():
            raise ValueError("model must be non-empty")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._transport = transport

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
            raise PlannerActionError("Ollama planner returned an invalid DiscoveryAction") from exc

    def _request_payload(self, context: DiscoveryContext) -> dict[str, Any]:
        context_data = {
            "grounded_input_ids": list(context.grounded_input_ids),
            "findings": list(context.findings),
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
                    "rationale": action.rationale,
                }
                for action in context.actions_taken
            ],
        }
        system = (
            "You are the bounded planning component of a scientific inquiry instrument. "
            "Choose exactly one next action from: question, hypothesis, prediction, "
            "experiment, stop. You are not an authority over truth. Never claim that "
            "generated text is evidence. Use only identifiers present in the supplied "
            "context. Prefer a discriminating experiment when competing hypotheses exist. "
            "When a GAP or TENSION finding has one hypothesis but no genuinely competing "
            "hypothesis, prefer proposing a distinct competing hypothesis grounded in that "
            "finding before stopping, when the finding permits one. "
            "If external evidence is required and the instrument cannot acquire it, stop. "
            "Return one JSON object only. The JSON field for the action type is named "
            "'kind', never 'action'. The only allowed JSON fields are: kind, target_ids, "
            "statement, consequence, consequences, conditions, objective, "
            "proposed_observation, discrimination_basis, rationale. Do not invent other "
            "field names. A hypothesis action creates a NEW hypothesis about a finding. "
            "For kind='question' or kind='hypothesis', target_ids MUST contain exactly "
            "one existing GAP or TENSION finding id. NEVER put an existing hypothesis id "
            "in target_ids for a hypothesis action. Example: if the finding id is GAP_001, "
            "a new hypothesis must use target_ids=[\"GAP_001\"]. "
            "For kind='prediction', target_ids MUST contain at least two existing "
            "hypothesis ids, because a prediction compares hypotheses. For prediction, "
            "conditions plus either consequence or consequences are required. "
            "For kind='experiment', target_ids MUST contain at least two existing "
            "prediction ids and conditions, objective, proposed_observation, and "
            "discrimination_basis are required. For kind='stop', rationale is required. "
            "Always include rationale. If feedback is supplied, it describes a rejected prior action; correct the action instead of repeating the same error."
        )
        return {
            "model": self.model,
            "stream": False,
            "format": "json",
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
