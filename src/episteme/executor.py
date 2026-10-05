"""Bounded experiment execution against grounded Episteme records.

Executors are deliberately separate from planners. A planner proposes an
experiment; an executor performs a concrete, bounded operation and records
the observed result. Executors never manufacture epistemic conclusions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Mapping, Protocol
from uuid import uuid4

from .model import ExperimentProposal, Provenance, Record, RecordKind, SCHEMA_VERSION
from .store import Store


@dataclass(frozen=True, slots=True)
class ExecutableExperimentSpec:
    """A small, machine-readable experiment vocabulary owned by Episteme.

    This is deliberately not a Python callable, module path, shell command,
    URL, or arbitrary evaluator configuration. Model-generated plans may name
    only operations registered by host code and may supply only the typed
    parameters defined by that operation.
    """

    operation: str
    position: float
    position_key: str = "position"
    expected_presence: Mapping[str, bool] = ()

    def __post_init__(self) -> None:
        if self.operation != "positional_presence":
            raise ValueError(f"unsupported executable experiment operation: {self.operation}")
        if isinstance(self.position, bool) or not isinstance(self.position, (int, float)):
            raise ValueError("position must be numeric")
        if not math.isfinite(float(self.position)):
            raise ValueError("position must be finite")
        if not isinstance(self.position_key, str) or not self.position_key.strip():
            raise ValueError("position_key must be a non-empty string")
        if not isinstance(self.expected_presence, Mapping):
            raise ValueError("expected_presence must be a mapping")
        for prediction_id, expected in self.expected_presence.items():
            if not isinstance(prediction_id, str) or not prediction_id.strip():
                raise ValueError("expected_presence keys must be non-empty strings")
            if not isinstance(expected, bool):
                raise ValueError("expected_presence values must be booleans")


def build_registered_experiment_runtime(
    spec: ExecutableExperimentSpec,
) -> tuple["PositionalObservationExecutor", Callable[..., object]]:
    """Resolve one allowlisted operation to host-owned executable semantics.

    The planner supplies data; this function supplies the code. No planner
    field can select a callable or alter the executor/evaluator implementation.
    """

    if spec.operation != "positional_presence":
        raise ValueError(f"unsupported executable experiment operation: {spec.operation}")

    from .evaluator import PositionalPredictionEvaluator

    executor = PositionalObservationExecutor(position_key=spec.position_key)
    evaluator_factory = lambda proposal, predictions: PositionalPredictionEvaluator(
        position=float(spec.position),
        expected_presence=dict(spec.expected_presence),
    )
    return executor, evaluator_factory


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
