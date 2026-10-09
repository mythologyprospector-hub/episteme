#!/usr/bin/env python3
"""Phase 29 review-3 benchmark: baseline, multiple properties, and blinding."""

from __future__ import annotations

import json
import math
import os
import re
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


_BLINDED_ELEMENT_NAMES = ("silicon", "tin", "germanium")
_BLINDED_ELEMENT_PATTERN = re.compile(
    r"\b(?:" + "|".join(re.escape(name) for name in _BLINDED_ELEMENT_NAMES) + r")\b",
    re.IGNORECASE,
)


def _contains_blinded_element_name(text: str) -> bool:
    """Return whether a complete element name appears, not a mere substring."""
    return _BLINDED_ELEMENT_PATTERN.search(text) is not None


def _index_evaluations(predictions, evaluations) -> tuple[dict[str, Any], bool]:
    """Associate each evaluation by prediction ID and report integrity explicitly."""
    expected_ids = {prediction.id for prediction in predictions}
    by_prediction_id: dict[str, Any] = {}
    duplicate_evaluation = False
    for evaluation in evaluations:
        if evaluation.prediction_id in by_prediction_id:
            duplicate_evaluation = True
        by_prediction_id[evaluation.prediction_id] = evaluation
    integrity_ok = (
        not duplicate_evaluation
        and len(evaluations) == len(predictions)
        and set(by_prediction_id) == expected_ids
    )
    return by_prediction_id, integrity_ok


class TracingOllamaPlanner(OllamaPlanner):
    def __init__(self, *args: Any, held_out_id: str, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.held_out_id = held_out_id
        self.contexts: list[dict[str, Any]] = []
        self.model_payloads: list[dict[str, Any]] = []

    def _request_payload(self, context):
        # Capture the actual transformed payload that choose() will send to Ollama.
        payload = super()._request_payload(context)
        self.model_payloads.append(payload)
        return payload

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


def _validate_experiment_evidence(store, predictions, evaluations, held_out_id: str, property_key: str) -> bool:
    """Require a persisted result for this held-out case and its exact proposal."""
    prediction_ids = {prediction.id for prediction in predictions}
    if not prediction_ids or any(
        prediction.predicted_numeric_value is None
        or not math.isfinite(float(prediction.predicted_numeric_value))
        for prediction in predictions
    ):
        return False

    for result in store.iter_records(kind="result"):
        payload = result.payload
        if payload.get("executor") != "phase29_rediscovery":
            continue
        if payload.get("property_key") != property_key:
            continue
        if payload.get("input_ids") != [held_out_id]:
            continue
        proposal_id = payload.get("experiment_proposal_id")
        if not proposal_id:
            continue
        proposal = store.get_experiment_proposal(proposal_id)
        if proposal is None or set(proposal.prediction_ids) != prediction_ids:
            continue
        if len(evaluations) != len(predictions):
            continue
        if any(
            evaluation.result_id != result.id
            or evaluation.experiment_proposal_id != proposal.id
            for evaluation in evaluations
        ):
            continue
        return True
    return False


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
        evaluations_by_prediction, evaluation_integrity_ok = _index_evaluations(
            predictions, evaluations
        )
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
        experiment_evidence_ok = _validate_experiment_evidence(
            store, predictions, evaluations, fixture.held_out_record.id, property_key
        )
        successful_forecast = (
            evaluation_integrity_ok
            and experiment_evidence_ok
            and len(evaluations) == len(predictions)
            and all(
                evaluation.outcome is PredictionEvaluationOutcome.CONSISTENT
                for evaluation in evaluations
            )
        )
        hidden_ok = all(
            item.get("id") != fixture.held_out_record.id
            for context in planner.contexts
            for item in context["grounded_observations"]
        )
        blind_names_ok = True
        if blinded:
            model_facing_text = "\\n".join(
                json.dumps(payload, sort_keys=True) for payload in planner.model_payloads
            )
            blind_names_ok = not _contains_blinded_element_name(model_facing_text)

        print(f"\\nPROPERTY: {case.display_name}")
        print(f"mode: {'blinded' if blinded else 'named'}")
        print(f"held-out value: {fixture.held_out_record.payload[property_key]}")
        print(f"tolerance: {case.tolerance:.3f}")
        print(f"baseline midpoint: {baseline:.6g}")
        print("hypotheses:")
        seen_hypotheses: set[str] = set()
        for context in planner.contexts:
            for hypothesis in context["hypotheses"]:
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
        for prediction in predictions:
            evaluation = evaluations_by_prediction.get(prediction.id)
            if evaluation is None:
                print(
                    f"prediction {prediction.id[:8]}: value={prediction.predicted_numeric_value} "
                    "verdict=NO EVALUATION"
                )
                continue
            print(
                f"prediction {prediction.id[:8]}: value={prediction.predicted_numeric_value} "
                f"verdict={evaluation.outcome.value} {evaluation.rationale}"
            )
        print(f"action sequence: {kinds}")
        print(f"evaluation records correctly matched by prediction ID: {evaluation_integrity_ok}")
        print(f"persisted experiment evidence valid: {experiment_evidence_ok}")
        print(
            "every forecast met tolerance and matched or beat baseline: "
            f"{successful_forecast}"
        )
        print(f"held-out hidden: {hidden_ok}; blinded names hidden: {blind_names_ok}")

        passed = (
            path_ok
            and stop_ok
            and distinct_ok
            and evaluation_integrity_ok
            and successful_forecast
            and hidden_ok
            and blind_names_ok
        )
        print(
            "ACCEPTANCE: PASS — every evaluated forecast met tolerance and matched or beat baseline"
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
