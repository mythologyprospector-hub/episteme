#!/usr/bin/env python3
"""Phase 29 review-2 benchmark: baseline, multiple properties, and blinding."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from episteme.autonomy import ExperimentRuntime, PositionalGapDiscoveryRuntime, run_autonomous_discovery
from episteme.model import PredictionEvaluationOutcome
from episteme.ollama import OllamaPlanner
from episteme.rediscovery import (
    REDISCOVERY_CASES,
    RediscoveryExperimentExecutor,
    RediscoveryPredictionEvaluator,
    build_mendeleev_fixture,
    derive_adjacent_midpoint,
)
from episteme.store import Store


class TracingOllamaPlanner(OllamaPlanner):
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
        if any(item.get("id") == self.held_out_id for item in context.grounded_observations):
            raise RuntimeError("held-out record leaked into Ollama grounded context")
        return super().choose(context)


def run_case(model: str, timeout: float, property_key: str, blinded: bool) -> tuple[bool, list[float]]:
    fixture = build_mendeleev_fixture()
    case = next(item for item in REDISCOVERY_CASES if item.property_key == property_key)
    baseline = derive_adjacent_midpoint(fixture.pre_discovery_records, property_key=property_key)

    with Store() as store:
        for record in fixture.pre_discovery_records + (fixture.held_out_record,):
            store.put_record(record)

        planner = TracingOllamaPlanner(
            model,
            timeout=timeout,
            host_capabilities=("historical_rediscovery",),
            rediscovery_property=property_key,
            blinded_rediscovery=blinded,
            held_out_id=fixture.held_out_record.id,
        )
        experiment_runtime = ExperimentRuntime(
            executor=RediscoveryExperimentExecutor(property_key=property_key),
            evaluator_factory=lambda proposal, predictions: RediscoveryPredictionEvaluator(
                pre_discovery_records=fixture.pre_discovery_records,
                property_key=property_key,
                tolerance=case.tolerance,
            ),
            comparison_conditions=f"historical fixture {case.display_name}",
        )
        result = run_autonomous_discovery(
            store,
            planner,
            grounded_input_ids=tuple(record.id for record in fixture.pre_discovery_records),
            started_at="1885-12-31T00:00:00+00:00",
            experiment_input_ids=(fixture.held_out_record.id,),
            max_steps=6,
            experiment_runtime=experiment_runtime,
            structural_discovery_runtime=PositionalGapDiscoveryRuntime(
                input_ids=tuple(record.id for record in fixture.pre_discovery_records),
                position_key="period",
                step=1.0,
            ),
            max_retries_per_step=2,
        )

        predictions = tuple(store.iter_predictions())
        evaluations = tuple(store.iter_prediction_evaluations())
        kinds = [step.action.kind for step in result.steps]
        required = ("discover_gap", "hypothesis", "hypothesis", "prediction", "experiment")
        position = 0
        for kind in kinds:
            if position < len(required) and kind == required[position]:
                position += 1

        path_ok = position == len(required)
        stop_ok = result.status == "stopped" and bool(result.stop_reason)
        distinct_ok = (
            len(predictions) >= 2
            and len({float(p.predicted_numeric_value) for p in predictions}) == len(predictions)
        )
        eval_ok = len(evaluations) == len(predictions) and all(
            item.outcome is PredictionEvaluationOutcome.CONSISTENT for item in evaluations
        )
        hidden_ok = all(
            item.get("id") != fixture.held_out_record.id
            for context in planner.contexts
            for item in context["grounded_observations"]
        )
        blind_names_ok = True
        if blinded:
            text = str(planner.contexts).lower()
            blind_names_ok = not any(name in text for name in ("silicon", "tin", "germanium"))

        print(f"\nPROPERTY: {case.display_name}")
        print(f"mode: {'blinded' if blinded else 'named'}")
        print(f"held-out value: {fixture.held_out_record.payload[property_key]}")
        print(f"tolerance: {case.tolerance:.3f}")
        print(f"baseline midpoint: {baseline:.6g}")
        print("hypotheses:")
        seen_hypotheses: set[str] = set()
        for context in planner.contexts:
            for hypothesis in context["hypotheses"]:
                # Ollama context snapshots are JSON-shaped dictionaries.
                hypothesis_id = str(hypothesis["id"])
                if hypothesis_id in seen_hypotheses:
                    continue
                seen_hypotheses.add(hypothesis_id)
                print(f"  {hypothesis_id[:8]}: {hypothesis.get('statement', '')}")
                rationale = hypothesis.get("rationale")
                if rationale:
                    print(f"    rationale: {rationale}")
                assumptions = hypothesis.get("assumptions") or []
                if assumptions:
                    print(f"    assumptions: {'; '.join(assumptions)}")
        print(f"stop reason: {result.stop_reason}")
        for prediction, evaluation in zip(predictions, evaluations):
            print(
                f"prediction {prediction.id[:8]}: value={prediction.predicted_numeric_value} "
                f"verdict={evaluation.outcome.value} {evaluation.rationale}"
            )
        print(f"action sequence: {kinds}")
        print(f"model error <= baseline error: {eval_ok}")
        print(f"held-out hidden: {hidden_ok}; blinded names hidden: {blind_names_ok}")

        passed = path_ok and stop_ok and distinct_ok and eval_ok and hidden_ok and blind_names_ok
        print(
            "ACCEPTANCE: PASS — evaluated forecast matched or beat the host baseline"
            if passed else
            "ACCEPTANCE: FAIL"
        )
        return passed, [
            float(p.predicted_numeric_value)
            for p in predictions
            if p.predicted_numeric_value is not None
        ]


def main() -> int:
    model = os.environ.get("EPISTEME_OLLAMA_MODEL", "qwen3:8b")
    timeout = float(os.environ.get("EPISTEME_OLLAMA_TIMEOUT", "300"))
    runs = int(os.environ.get("EPISTEME_OLLAMA_RUNS", "1"))
    blind = os.environ.get("EPISTEME_OLLAMA_BLIND", "0") == "1"
    if runs < 1:
        raise SystemExit("EPISTEME_OLLAMA_RUNS must be >= 1")

    overall = True
    for case in REDISCOVERY_CASES:
        outcomes = []
        values = []
        for _ in range(runs):
            passed, predictions = run_case(model, timeout, case.property_key, blind)
            outcomes.append(passed)
            values.extend(predictions)
        pass_rate = sum(outcomes) / len(outcomes)
        spread = (max(values) - min(values)) if values else float("nan")
        print(
            f"SUMMARY {case.display_name}: N={runs} pass_rate={pass_rate:.0%} "
            f"prediction_spread={spread:.6g}"
        )
        overall = overall and all(outcomes)

    print(f"MODEL: {model}")
    print(f"OVERALL: {'PASS' if overall else 'FAIL'}")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
