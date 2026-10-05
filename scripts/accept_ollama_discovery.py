#!/usr/bin/env python3
"""Manual acceptance run for the real Ollama-backed discovery planner.

This is intentionally separate from pytest: it exercises the local model,
while the deterministic autonomy/runtime tests remain CI-safe.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


# Allow this acceptance script to run directly from a source checkout without
# requiring the caller to preconfigure PYTHONPATH.
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from episteme.autonomy import run_autonomous_discovery
from episteme.discovery import detect_positional_gap
from episteme.model import Provenance, Record, RecordKind
from episteme.ollama import OllamaPlanner
from episteme.store import Store


CREATED = "2026-10-05T00:00:00Z"
PROVENANCE = (
    Provenance(
        source_id="ollama-acceptance",
        captured_at=CREATED,
        source_location="https://example.org/ollama-acceptance",
        source_version="1",
    ),
)


class TracingOllamaPlanner(OllamaPlanner):
    """Acceptance-only planner that prints the raw model response."""

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

    records = tuple(
        Record(
            id=f"aaaaaaaa-{index:04d}-4aaa-8aaa-aaaaaaaaaaaa",
            kind=RecordKind.OBSERVATION,
            payload={"position": position},
            provenance=PROVENANCE,
            created_at=CREATED,
        )
        for index, position in enumerate((1.0, 2.0, 4.0), start=1)
    )

    with Store() as store:
        for record in records:
            store.put_record(record)

        gap = detect_positional_gap(
            store,
            record_ids=tuple(record.id for record in records),
            position_key="position",
            step=1.0,
            created_at=CREATED,
        )
        if gap is None:
            raise RuntimeError("acceptance fixture did not produce a positional gap")
        store.put_discovery_finding(gap)

        planner = TracingOllamaPlanner(model, timeout=timeout)
        result = run_autonomous_discovery(
            store,
            planner,
            grounded_input_ids=tuple(record.id for record in records),
            started_at=CREATED,
            max_steps=6,
            max_retries_per_step=2,
        )

        print(f"model: {model}")
        print(f"status: {result.status}")
        print(f"stop_reason: {result.stop_reason}")
        for index, step in enumerate(result.steps, start=1):
            action = step.action
            print(
                f"step {index}: {action.kind} "
                f"targets={list(action.target_ids)} "
                f"rationale={action.rationale!r}"
            )
            if step.output_ids:
                print(f"         outputs={list(step.output_ids)}")

        kinds = [step.action.kind for step in result.steps]

        experiments = tuple(store.iter_experiment_proposals())
        evaluations = tuple(store.iter_prediction_evaluations())
        consequences = tuple(store.iter_knowledge_state_consequences())
        executable_experiments = tuple(
            item for item in experiments if item.execution_spec is not None
        )
        print(f"persisted experiments: {len(experiments)}")
        print(f"evaluations: {len(evaluations)}")
        print(f"knowledge-state consequences: {len(consequences)}")

        print(f"action sequence: {kinds}")

        required = ("hypothesis", "hypothesis", "prediction", "experiment")
        position = 0
        for kind in kinds:
            if position < len(required) and kind == required[position]:
                position += 1

        if position < len(required):
            print(
                "ACCEPTANCE: FAIL — the real planner did not reach the "
                "full hypothesis → competing hypothesis → prediction → "
                "experiment path within the bound."
            )
            return 1

        if len(executable_experiments) != 1:
            print(
                "ACCEPTANCE: FAIL — the real planner reached an experiment, "
                "but no single persisted executable experiment was found."
            )
            return 1
        if len(evaluations) != 2 or len(consequences) != 2:
            print(
                "ACCEPTANCE: FAIL — the executable experiment did not complete "
                "the expected two-prediction evaluation/consequence cycle."
            )
            return 1

        spec = executable_experiments[0].execution_spec
        expected_ids = set(executable_experiments[0].prediction_ids)
        if not isinstance(spec, dict) or spec.get("operation") != "positional_presence":
            print("ACCEPTANCE: FAIL — persisted execution spec is not the registered operation.")
            return 1
        if set(spec.get("expected_presence", {})) != expected_ids:
            print("ACCEPTANCE: FAIL — persisted executable expectations do not match prediction ids.")
            return 1

        print(
            "ACCEPTANCE: PASS — the real Ollama planner drove the bounded loop "
            "through competing hypotheses, prediction, executable experiment, "
            "deterministic evaluation, and knowledge-state consequences."
        )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
