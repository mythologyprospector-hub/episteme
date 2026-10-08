#!/usr/bin/env python3
"""Manual acceptance run for the real Ollama-backed Phase 29 rediscovery path.

The held-out record is stored on the host but is never included in the
planner's grounded context. Ollama proposes the bounded discovery actions and
numeric forecast; the host owns the held-out experiment executor and
deterministic evaluator.
"""

from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from episteme.autonomy import (
    ExperimentRuntime,
    PositionalGapDiscoveryRuntime,
    run_autonomous_discovery,
)
from episteme.model import PredictionEvaluationOutcome
from episteme.ollama import OllamaPlanner
from episteme.rediscovery import (
    RediscoveryExperimentExecutor,
    RediscoveryPredictionEvaluator,
    build_mendeleev_fixture,
)
from episteme.store import Store


class TracingOllamaPlanner(OllamaPlanner):
    """Acceptance-only planner that prints raw responses and captures contexts."""

    def __init__(self, *args: Any, held_out_id: str, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.held_out_id = held_out_id
        self.contexts: list[dict[str, Any]] = []

    def choose(self, context):
        snapshot = {
            "grounded_observations": list(context.grounded_observations),
            "findings": list(context.findings),
            "hypotheses": list(context.hypotheses),
            "predictions": list(context.predictions),
            "experiments": list(context.experiments),
        }
        self.contexts.append(snapshot)
        if any(
            observation.get("id") == self.held_out_id
            for observation in context.grounded_observations
        ):
            raise RuntimeError("held-out record leaked into Ollama grounded context")
        return super().choose(context)

    def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = super()._request(payload)
        content = response.get("message", {}).get("content")
        print("\n--- Ollama response ---")
        if isinstance(content, str):
            print(content)
        else:
            print(json.dumps(response, indent=2, sort_keys=True))
        print("--- end Ollama response ---")
        return response


def main() -> int:
    model = os.environ.get("EPISTEME_OLLAMA_MODEL", "qwen3:8b")
    timeout = float(os.environ.get("EPISTEME_OLLAMA_TIMEOUT", "180"))
    fixture = build_mendeleev_fixture()

    with Store() as store:
        for record in fixture.pre_discovery_records + (fixture.held_out_record,):
            store.put_record(record)

        planner = TracingOllamaPlanner(
            model,
            timeout=timeout,
            host_capabilities=("historical_rediscovery",),
            held_out_id=fixture.held_out_record.id,
        )

        experiment_runtime = ExperimentRuntime(
            executor=RediscoveryExperimentExecutor(),
            evaluator_factory=lambda proposal, predictions: RediscoveryPredictionEvaluator(
                pre_discovery_records=fixture.pre_discovery_records,
                tolerance=0.05,
            ),
            comparison_conditions="historical fixture relative atomic mass",
        )

        result = run_autonomous_discovery(
            store,
            planner,
            grounded_input_ids=tuple(
                record.id for record in fixture.pre_discovery_records
            ),
            started_at="1885-12-31T00:00:00+00:00",
            experiment_input_ids=(fixture.held_out_record.id,),
            max_steps=6,
            experiment_runtime=experiment_runtime,
            structural_discovery_runtime=PositionalGapDiscoveryRuntime(
                input_ids=tuple(
                    record.id for record in fixture.pre_discovery_records
                ),
                position_key="period",
                step=1.0,
            ),
            max_retries_per_step=2,
        )

        kinds = [step.action.kind for step in result.steps]
        experiments = tuple(store.iter_experiment_proposals())
        predictions = tuple(store.iter_predictions())
        evaluations = tuple(store.iter_prediction_evaluations())
        consequences = tuple(store.iter_knowledge_state_consequences())

        print(f"model: {model}")
        print(f"status: {result.status}")
        print(f"stop_reason: {result.stop_reason}")
        print(f"action sequence: {kinds}")
        print(f"predictions: {len(predictions)}")
        print(f"experiments: {len(experiments)}")
        print(f"evaluations: {len(evaluations)}")
        print(f"knowledge-state consequences: {len(consequences)}")

        required = ("discover_gap", "hypothesis", "hypothesis", "prediction", "experiment")
        position = 0
        for kind in kinds:
            if position < len(required) and kind == required[position]:
                position += 1

        if position < len(required):
            print("ACCEPTANCE: FAIL — Ollama did not reach the complete Phase 29 action path.")
            return 1

        if result.status != "stopped":
            print("ACCEPTANCE: FAIL — bounded rediscovery did not terminate cleanly.")
            return 1

        if len(experiments) != 1:
            print("ACCEPTANCE: FAIL — expected exactly one rediscovery experiment.")
            return 1

        spec = experiments[0].execution_spec
        if not isinstance(spec, dict) or spec.get("operation") != "historical_rediscovery":
            print("ACCEPTANCE: FAIL — experiment did not use the historical_rediscovery operation.")
            return 1

        if len(predictions) < 2:
            print("ACCEPTANCE: FAIL — expected competing quantitative predictions.")
            return 1

        numeric_predictions = [
            float(item.predicted_numeric_value)
            for item in predictions
            if item.predicted_numeric_value is not None
        ]
        if len(numeric_predictions) != len(predictions):
            print("ACCEPTANCE: FAIL — every rediscovery prediction needs a numeric forecast.")
            return 1

        if not all(math.isclose(value, 73.4, rel_tol=0.0, abs_tol=0.01) for value in numeric_predictions):
            print(f"ACCEPTANCE: FAIL — Ollama forecasts were not the expected bounded value: {numeric_predictions}")
            return 1

        if len(evaluations) != len(predictions):
            print("ACCEPTANCE: FAIL — every prediction must receive a deterministic evaluation.")
            return 1

        if any(item.outcome is not PredictionEvaluationOutcome.CONSISTENT for item in evaluations):
            print("ACCEPTANCE: FAIL — one or more rediscovery evaluations were inconsistent.")
            return 1

        if not all(
            "72.32" in item.rationale and "73.4" in item.rationale
            for item in evaluations
        ):
            print("ACCEPTANCE: FAIL — deterministic evaluation did not record expected and observed values.")
            return 1

        if len(consequences) != len(evaluations):
            print("ACCEPTANCE: FAIL — evaluation consequences were not recorded.")
            return 1

        if any(
            observation.get("id") == fixture.held_out_record.id
            for context in planner.contexts
            for observation in context["grounded_observations"]
        ):
            print("ACCEPTANCE: FAIL — held-out observation leaked into planner context.")
            return 1

        print(
            "ACCEPTANCE: PASS — Ollama drove historical rediscovery from earlier "
            "observations through a bounded gap, competing hypotheses, quantitative "
            "prediction, host-owned held-out execution, and deterministic evaluation "
            "without seeing the held-out observation."
        )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
