#!/usr/bin/env python3
"""Real Ollama acceptance for the complete bounded discovery chain."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from episteme.autonomy import (
    ExplorationAdmissionRuntime,
    ExplorationAssessmentRuntime,
    PositionalExplorationRuntime,
    PositionalGapDiscoveryRuntime,
    run_autonomous_discovery,
)
from episteme.model import Provenance, Record, RecordKind
from episteme.ollama import OllamaPlanner
from episteme.store import Store

CREATED = "2026-10-06T00:00:00Z"
PROVENANCE = (
    Provenance(
        source_id="ollama-full-chain-acceptance",
        captured_at=CREATED,
        source_location="fixture://ollama-full-chain",
        source_version="1",
    ),
)


def main() -> int:
    model = os.environ.get("EPISTEME_OLLAMA_MODEL", "qwen3:8b")
    timeout = float(os.environ.get("EPISTEME_OLLAMA_TIMEOUT", "180"))
    records = tuple(
        Record(
            id=f"cccccccc-{i:04d}-4aaa-8aaa-cccccccccccc",
            kind=RecordKind.OBSERVATION,
            payload={"position": float(position)},
            provenance=PROVENANCE,
            created_at=CREATED,
        )
        for i, position in enumerate((1.0, 2.0, 4.0), start=1)
    )
    input_ids = tuple(item.id for item in records)

    with Store() as store:
        for record in records:
            store.put_record(record)

        result = run_autonomous_discovery(
            store,
            OllamaPlanner(model, timeout=timeout),
            grounded_input_ids=input_ids,
            started_at=CREATED,
            max_steps=12,
            max_retries_per_step=2,
            exploration_runtime=PositionalExplorationRuntime(
                input_ids=input_ids, position_key="position", max_records=3
            ),
            structural_discovery_runtime=PositionalGapDiscoveryRuntime(
                input_ids=input_ids, position_key="position", step=1.0
            ),
            exploration_assessment_runtime=ExplorationAssessmentRuntime(
                allowed_input_ids=input_ids,
                accepted=True,
                method="ollama-full-chain-host-assessment",
                method_version="1",
                rationale="Acceptance fixture permits generated exploration into discovery context.",
                provenance=PROVENANCE,
            ),
            exploration_admission_runtime=ExplorationAdmissionRuntime(
                allowed_input_ids=input_ids
            ),
        )

        actions = [step.action.kind for step in result.steps]
        hypotheses = tuple(store.iter_hypotheses())
        predictions = tuple(store.iter_predictions())
        experiments = tuple(store.iter_experiment_proposals())
        evaluations = tuple(store.iter_prediction_evaluations())

        print("model:", model)
        print("status:", result.status)
        print("stop_reason:", result.stop_reason)
        print("actions:", actions)
        print("hypotheses:", len(hypotheses))
        print("predictions:", len(predictions))
        print("experiments:", len(experiments))
        print("evaluations:", len(evaluations))

        required = (
            "scout",
            "assess_exploration",
            "admit_exploration",
            "discover_gap",
            "hypothesis",
            "hypothesis",
            "prediction",
            "experiment",
        )
        cursor = 0
        for action in actions:
            if cursor < len(required) and action == required[cursor]:
                cursor += 1

        if (
            result.status != "stopped"
            or cursor < len(required)
            or len(hypotheses) < 2
            or len(predictions) < 2
            or len(experiments) != 1
            or len(evaluations) != 2
        ):
            print("ACCEPTANCE: FAIL — complete bounded discovery chain did not finish.")
            return 1

        if actions[-1] != "experiment":
            print("ACCEPTANCE: FAIL — bounded chain did not terminate immediately after experiment execution.")
            return 1

        if any(item.input_ids != input_ids for item in hypotheses):
            print("ACCEPTANCE: FAIL — hypothesis grounded-input lineage changed.")
            return 1

        print(
            "ACCEPTANCE: PASS — Ollama drove exploration, admission, structural discovery, "
            "competing hypotheses, discriminating predictions, and bounded experiment/evaluation."
        )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
