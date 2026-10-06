#!/usr/bin/env python3
"""Manual acceptance run for Ollama-driven exploration -> assessment -> admission."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from episteme.autonomy import (
    ExplorationAdmissionRuntime,
    ExplorationAssessmentRuntime,
    PositionalExplorationRuntime,
    run_autonomous_discovery,
)
from episteme.model import Provenance, Record, RecordKind
from episteme.ollama import OllamaPlanner
from episteme.store import Store


CREATED = "2026-10-06T00:00:00Z"
PROVENANCE = (
    Provenance(
        source_id="ollama-exploration-acceptance",
        captured_at=CREATED,
        source_location="fixture://ollama-exploration",
        source_version="1",
    ),
)


class TracingOllamaPlanner(OllamaPlanner):
    def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = super()._request(payload)
        content = response.get("message", {}).get("content")
        print("\n--- Ollama response ---")
        print(content if isinstance(content, str) else json.dumps(response, indent=2, sort_keys=True))
        print("--- end Ollama response ---")
        return response


def main() -> int:
    model = os.environ.get("EPISTEME_OLLAMA_MODEL", "qwen3:8b")
    timeout = float(os.environ.get("EPISTEME_OLLAMA_TIMEOUT", "180"))

    records = tuple(
        Record(
            id=f"bbbbbbbb-{index:04d}-4aaa-8aaa-bbbbbbbbbbbb",
            kind=RecordKind.OBSERVATION,
            payload={"position": float(position)},
            provenance=PROVENANCE,
            created_at=CREATED,
        )
        for index, position in enumerate((1.0, 2.0, 4.0), start=1)
    )
    input_ids = tuple(record.id for record in records)

    with Store() as store:
        for record in records:
            store.put_record(record)

        planner = TracingOllamaPlanner(model, timeout=timeout)
        result = run_autonomous_discovery(
            store,
            planner,
            grounded_input_ids=input_ids,
            started_at=CREATED,
            max_steps=5,
            max_retries_per_step=2,
            exploration_runtime=PositionalExplorationRuntime(
                input_ids=input_ids,
                position_key="position",
                max_records=3,
            ),
            exploration_assessment_runtime=ExplorationAssessmentRuntime(
                allowed_input_ids=input_ids,
                accepted=True,
                method="ollama-acceptance-host-assessment",
                method_version="1",
                rationale="Acceptance fixture permits this generated observation into discovery context.",
                provenance=PROVENANCE,
            ),
            exploration_admission_runtime=ExplorationAdmissionRuntime(
                allowed_input_ids=input_ids,
            ),
        )

        kinds = [step.action.kind for step in result.steps]
        observations = tuple(store.iter_exploration_observations())
        assessments = tuple(store.iter_exploration_observation_assessments())
        findings = tuple(store.iter_discovery_findings())

        print(f"model: {model}")
        print(f"status: {result.status}")
        print(f"stop_reason: {result.stop_reason}")
        print(f"action sequence: {kinds}")
        print(f"observations: {len(observations)}")
        print(f"assessments: {len(assessments)}")
        print(f"discovery findings: {len(findings)}")

        required = ("scout", "assess_exploration", "admit_exploration")
        position = 0
        for kind in kinds:
            if position < len(required) and kind == required[position]:
                position += 1

        if position < len(required):
            print(
                "ACCEPTANCE: FAIL — the real Ollama planner did not drive "
                "scout -> assessment -> explicit admission within the bound."
            )
            return 1

        if len(observations) != 1 or len(assessments) != 1 or len(findings) != 1:
            print("ACCEPTANCE: FAIL — expected exactly one observation, assessment, and finding.")
            return 1

        observation = observations[0]
        assessment = assessments[0]
        finding = findings[0]

        if not assessment.accepted:
            print("ACCEPTANCE: FAIL — host acceptance policy was not persisted as accepted.")
            return 1
        if finding.input_ids != input_ids:
            print("ACCEPTANCE: FAIL — finding lost the original grounded input lineage.")
            return 1
        if observation.id not in finding.context_ids or assessment.id not in finding.context_ids:
            print("ACCEPTANCE: FAIL — finding does not preserve generated observation/assessment context.")
            return 1
        if store.get_record(observation.id) is not None:
            print("ACCEPTANCE: FAIL — generated observation became a grounded record.")
            return 1

        print(
            "ACCEPTANCE: PASS — Qwen drove bounded scouting, host-owned assessment, "
            "explicit admission, and preserved generated-versus-grounded lineage."
        )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
