"""Bounded experiment execution against grounded Episteme records.

Executors are deliberately separate from planners. A planner proposes an
experiment; an executor performs a concrete, bounded operation and records
the observed result. Executors never manufacture epistemic conclusions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol
from uuid import uuid4

from .model import ExperimentProposal, Provenance, Record, RecordKind, SCHEMA_VERSION
from .store import Store


class ExperimentExecutor(Protocol):
    def execute(
        self,
        store: Store,
        proposal: ExperimentProposal,
        *,
        input_ids: tuple[str, ...],
        created_at: str,
    ) -> Record:
        """Execute a bounded experiment and persist its grounded result."""


@dataclass(frozen=True, slots=True)
class PositionalObservationExecutor:
    """Measure numeric positions from existing observation records.

    This is intentionally narrow: it does not infer what a missing position
    means and it does not evaluate any prediction. It simply reads grounded
    observations, performs a deterministic measurement operation, and records
    what was actually observed.
    """

    position_key: str = "position"
    method: str = "positional_observation"
    method_version: str = "1"

    def execute(
        self,
        store: Store,
        proposal: ExperimentProposal,
        *,
        input_ids: tuple[str, ...],
        created_at: str,
    ) -> Record:
        if store.get_experiment_proposal(proposal.id) is None:
            raise ValueError("experiment executor requires a persisted proposal: " + proposal.id)
        if not input_ids:
            raise ValueError("positional observation requires at least one input record")

        positions: list[float] = []
        for record_id in input_ids:
            record = store.get_record(record_id)
            if record is None:
                raise ValueError("positional observation references missing record: " + record_id)
            if record.kind is not RecordKind.OBSERVATION:
                raise ValueError(
                    "positional observation requires observation records: " + record_id
                )
            value = record.payload.get(self.position_key)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(
                    f"observation {record_id} has no numeric {self.position_key!r}"
                )
            if not math.isfinite(float(value)):
                raise ValueError(
                    f"observation {record_id} has non-finite {self.position_key!r}"
                )
            positions.append(float(value))

        positions.sort()

        result = Record(
            id=str(uuid4()),
            kind=RecordKind.RESULT,
            payload={
                "executor": self.method,
                "executor_version": self.method_version,
                "experiment_proposal_id": proposal.id,
                "input_ids": list(input_ids),
                "position_key": self.position_key,
                "observed_positions": positions,
                "observation_count": len(positions),
            },
            provenance=(
                Provenance(
                    source_id=f"episteme://executor/{self.method}",
                    captured_at=created_at,
                    source_location=f"episteme://executor/{self.method}",
                    source_version=self.method_version,
                    note="Deterministic result produced by a bounded experiment executor.",
                ),
            ),
            created_at=created_at,
            schema_version=SCHEMA_VERSION,
        )
        store.put_record(result)
        return result
