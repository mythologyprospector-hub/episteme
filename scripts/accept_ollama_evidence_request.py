#!/usr/bin/env python3
"""Real Ollama acceptance for the host-owned Phase 28 evidence-request path."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from episteme.acquisition import AcquisitionResponse
from episteme.autonomy import (
    ExplorationAdmissionRuntime,
    ExplorationAssessmentRuntime,
    PositionalExplorationRuntime,
    PositionalGapDiscoveryRuntime,
    run_autonomous_discovery,
)
from episteme.capture import CaptureOutcome
from episteme.evidence_request import execute_evidence_request
from episteme.model import Provenance, Record, RecordKind
from episteme.ollama import OllamaPlanner
from episteme.store import Store

CREATED = "2026-10-06T00:00:00Z"
PROVENANCE = (
    Provenance(
        source_id="ollama-evidence-request-acceptance",
        captured_at=CREATED,
        source_location="fixture://ollama-evidence-request",
        source_version="1",
    ),
)


class FixtureEvidenceRuntime:
    """Host-owned fixture binding for the registered Crossref capability."""

    def request_evidence(self, store, request, *, created_at):
        return execute_evidence_request(
            request,
            store,
            provider=lambda _request: AcquisitionResponse(
                status=200,
                media_type="application/json",
                source_version="fixture-crossref-v1",
                content=b'{"message":{"items":[]}}',
                outcome=CaptureOutcome.COMPLETE,
            ),
            captured_at=created_at,
            capture_id="capture-ollama-evidence-request",
        )


def main() -> int:
    model = os.environ.get("EPISTEME_OLLAMA_MODEL", "qwen3:8b")
    timeout = float(os.environ.get("EPISTEME_OLLAMA_TIMEOUT", "180"))

    records = tuple(
        Record(
            id=f"dddddddd-{i:04d}-4aaa-8aaa-dddddddddddd",
            kind=RecordKind.OBSERVATION,
            payload={"position": float(position)},
            provenance=PROVENANCE,
            created_at=CREATED,
        )
        for i, position in enumerate((1.0, 2.0, 4.0), start=1)
    )
    held_out = Record(
        id="eeeeeeee-0001-4aaa-8aaa-eeeeeeeeeeee",
        kind=RecordKind.OBSERVATION,
        payload={"position": 3.0},
        provenance=PROVENANCE,
        created_at=CREATED,
    )
    input_ids = tuple(item.id for item in records)

    with Store() as store:
        for record in (*records, held_out):
            store.put_record(record)

        result = run_autonomous_discovery(
            store,
            OllamaPlanner(
                model,
                timeout=timeout,
                evidence_capabilities=("crossref_works",),
                host_capabilities=("scout", "assess_exploration", "admit_exploration", "discover_gap", "request_evidence"),
            ),
            grounded_input_ids=input_ids,
            experiment_input_ids=(held_out.id,),
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
                method="ollama-evidence-request-host-assessment",
                method_version="1",
                rationale="Acceptance fixture permits generated exploration into discovery context.",
                provenance=PROVENANCE,
            ),
            exploration_admission_runtime=ExplorationAdmissionRuntime(
                allowed_input_ids=input_ids
            ),
            evidence_request_runtime=FixtureEvidenceRuntime(),
        )

        actions = [step.action.kind for step in result.steps]
        captures = tuple(store.iter_captured_representations())

        print("model:", model)
        print("status:", result.status)
        print("stop_reason:", result.stop_reason)
        print("actions:", actions)
        print("captures:", len(captures))

        if result.status != "stopped":
            print("ACCEPTANCE: FAIL — bounded Ollama evidence-request run did not stop cleanly.")
            return 1

        if "request_evidence" not in actions:
            print("ACCEPTANCE: FAIL — real Ollama did not choose request_evidence.")
            return 1

        if actions[-1] != "request_evidence":
            print("ACCEPTANCE: FAIL — evidence request was not the terminal completed action.")
            return 1

        if len(captures) != 1 or captures[0].outcome is not CaptureOutcome.COMPLETE:
            print("ACCEPTANCE: FAIL — host-owned evidence runtime did not produce one complete capture.")
            return 1

        print(
            "ACCEPTANCE: PASS — Ollama selected a bounded evidence request and the "
            "host-owned runtime completed it through the registered capability."
        )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
