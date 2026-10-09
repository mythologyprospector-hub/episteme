"""Phase 29 historical rediscovery fixture and host-owned benchmark runtime.

The fixture separates pre-discovery observations from later held-out evidence.
The benchmark runtime derives a quantitative prediction only from the earlier
observations, then evaluates that prediction against the separately supplied
held-out observation.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from episteme.model import Prediction, PredictionEvaluation, PredictionEvaluationOutcome
from episteme.store import Store
from enum import Enum

from episteme.model import Provenance, Record, RecordKind

FIXTURE_CAPTURED_AT = "1885-12-31T00:00:00+00:00"
FIXTURE_SOURCE = "phase29-rsc-historical-fixture"
FIXTURE_VERSION = "1"
FIXTURE_LOCATION = "https://www.rsc.org/images/23_The_Periodic_Law_tcm18-30005.pdf"


@dataclass(frozen=True)
class RediscoveryFixture:
    pre_discovery_records: tuple[Record, ...]
    held_out_record: Record


@dataclass(frozen=True)
class RediscoveryBenchmarkCase:
    property_key: str
    display_name: str
    tolerance: float = 0.05


REDISCOVERY_CASES = (
    RediscoveryBenchmarkCase("relative_atomic_mass", "relative atomic mass"),
    RediscoveryBenchmarkCase("density_g_cm3", "density (g/cm^3)"),
    RediscoveryBenchmarkCase("melting_point_c", "melting point (C)"),
)


class RediscoveryOutcome(str, Enum):
    MATCHED = "matched"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass(frozen=True)
class RediscoveryPrediction:
    predicted_relative_atomic_mass: float
    input_ids: tuple[str, ...]
    method: str
    method_version: str


@dataclass(frozen=True)
class RediscoveryEvaluation:
    outcome: RediscoveryOutcome
    predicted_relative_atomic_mass: float
    observed_relative_atomic_mass: float
    absolute_error: float
    relative_error: float
    tolerance: float


def _provenance() -> tuple[Provenance, ...]:
    return (
        Provenance(
            source_id=FIXTURE_SOURCE,
            captured_at=FIXTURE_CAPTURED_AT,
            source_location=FIXTURE_LOCATION,
            source_version=FIXTURE_VERSION,
            note="Bounded pre-discovery historical fixture; later discovery data is excluded.",
        ),
    )


def build_mendeleev_fixture() -> RediscoveryFixture:
    provenance = _provenance()

    pre_discovery = (
        Record(
            id="10000000-0000-4000-8000-000000000001",
            kind=RecordKind.OBSERVATION,
            payload={
                "label": "carbon",
                "family": "group_14",
                "period": 2,
                "relative_atomic_mass": 12.01,
                "density_g_cm3": 2.26,
                "melting_point_c": 3825.0,
            },
            provenance=provenance,
            created_at=FIXTURE_CAPTURED_AT,
        ),
        Record(
            id="10000000-0000-4000-8000-000000000002",
            kind=RecordKind.OBSERVATION,
            payload={
                "label": "silicon",
                "family": "group_14",
                "period": 3,
                "relative_atomic_mass": 28.085,
                "density_g_cm3": 2.3296,
                "melting_point_c": 1414.0,
            },
            provenance=provenance,
            created_at=FIXTURE_CAPTURED_AT,
        ),
        Record(
            id="10000000-0000-4000-8000-000000000003",
            kind=RecordKind.OBSERVATION,
            payload={
                "label": "tin",
                "family": "group_14",
                "period": 5,
                "relative_atomic_mass": 118.710,
                "density_g_cm3": 7.287,
                "melting_point_c": 231.928,
            },
            provenance=provenance,
            created_at=FIXTURE_CAPTURED_AT,
        ),
        Record(
            id="10000000-0000-4000-8000-000000000004",
            kind=RecordKind.OBSERVATION,
            payload={
                "label": "lead",
                "family": "group_14",
                "period": 6,
                "relative_atomic_mass": 207.2,
                "density_g_cm3": 11.3,
                "melting_point_c": 327.462,
            },
            provenance=provenance,
            created_at=FIXTURE_CAPTURED_AT,
        ),
    )

    held_out = Record(
        id="20000000-0000-4000-8000-000000000001",
        kind=RecordKind.OBSERVATION,
        payload={
            "label": "held_out_element",
            "family": "group_14",
            "period": 4,
            "relative_atomic_mass": 72.630,
            "density_g_cm3": 5.3234,
            "melting_point_c": 938.25,
        },
        provenance=provenance,
        created_at="1886-12-31T00:00:00+00:00",
    )

    return RediscoveryFixture(
        pre_discovery_records=pre_discovery,
        held_out_record=held_out,
    )


def derive_adjacent_midpoint(
    pre_discovery_records: tuple[Record, ...],
    *,
    property_key: str,
    missing_period: int = 4,
) -> float:
    candidates = [
        record
        for record in pre_discovery_records
        if record.payload.get("family") == "group_14"
    ]
    by_period = {int(record.payload["period"]): record for record in candidates}
    if missing_period in by_period:
        raise ValueError("pre-discovery inputs must not contain the held-out period")
    if missing_period - 1 not in by_period or missing_period + 1 not in by_period:
        raise ValueError("pre-discovery inputs must contain the adjacent periods")
    lower = by_period[missing_period - 1].payload.get(property_key)
    upper = by_period[missing_period + 1].payload.get(property_key)
    if lower is None or upper is None:
        raise ValueError(f"property is missing from adjacent observations: {property_key}")
    return (float(lower) + float(upper)) / 2.0


def derive_mendeleev_mass_prediction(
    pre_discovery_records: tuple[Record, ...],
) -> RediscoveryPrediction:
    """Derive a bounded mass prediction from the two observations around the gap.

    The runtime is deliberately blind to the held-out record. It selects the
    adjacent observed periods around the missing period-4 position and takes
    their midpoint. No later element identity or later measured value is used.
    """

    candidates = [
        record
        for record in pre_discovery_records
        if record.payload.get("family") == "group_14"
    ]
    by_period = {
        int(record.payload["period"]): record
        for record in candidates
    }
    if 4 in by_period:
        raise ValueError("pre-discovery inputs must not contain the held-out period")
    if 3 not in by_period or 5 not in by_period:
        raise ValueError("pre-discovery inputs must contain periods 3 and 5")

    lower = float(by_period[3].payload["relative_atomic_mass"])
    upper = float(by_period[5].payload["relative_atomic_mass"])
    prediction = (lower + upper) / 2.0

    return RediscoveryPrediction(
        predicted_relative_atomic_mass=prediction,
        input_ids=(by_period[3].id, by_period[5].id),
        method="adjacent-period-mass-midpoint",
        method_version="1",
    )


def evaluate_mendeleev_mass_prediction(
    prediction: RediscoveryPrediction,
    held_out_record: Record,
    tolerance: float = 0.05,
) -> RediscoveryEvaluation:
    """Evaluate the prediction against later held-out evidence.

    The evaluator receives the held-out record separately from the prediction
    inputs. A match is deterministic and uses only the pre-registered relative
    error tolerance.
    """

    if not 0 < tolerance < 1:
        raise ValueError("tolerance must be between 0 and 1")

    observed = float(held_out_record.payload["relative_atomic_mass"])
    predicted = prediction.predicted_relative_atomic_mass
    absolute_error = abs(predicted - observed)
    relative_error = absolute_error / observed

    if relative_error <= tolerance:
        outcome = RediscoveryOutcome.MATCHED
    else:
        outcome = RediscoveryOutcome.FAILED

    return RediscoveryEvaluation(
        outcome=outcome,
        predicted_relative_atomic_mass=predicted,
        observed_relative_atomic_mass=observed,
        absolute_error=absolute_error,
        relative_error=relative_error,
        tolerance=tolerance,
    )


@dataclass(frozen=True, slots=True)
class RediscoveryExperimentExecutor:
    """Host-owned executor for the Phase 29 held-out observation."""

    property_key: str = "relative_atomic_mass"
    method: str = "phase29_rediscovery"
    method_version: str = "1"

    def execute(self, store: Store, proposal, *, input_ids: tuple[str, ...], created_at: str) -> Record:
        if store.get_experiment_proposal(proposal.id) is None:
            raise ValueError("rediscovery executor requires a persisted proposal: " + proposal.id)
        if len(input_ids) != 1:
            raise ValueError("rediscovery experiment requires exactly one held-out input")
        held_out = store.get_record(input_ids[0])
        if held_out is None or held_out.kind is not RecordKind.OBSERVATION:
            raise ValueError("rediscovery experiment requires a held-out observation")
        observed = held_out.payload.get(self.property_key)
        if observed is None:
            raise ValueError("rediscovery experiment held-out record lacks property: " + self.property_key)
        observed = float(observed)
        result = Record(
            id=str(uuid4()),
            kind=RecordKind.RESULT,
            payload={
                "executor": self.method,
                "executor_version": self.method_version,
                "experiment_proposal_id": proposal.id,
                "input_ids": list(input_ids),
                "property_key": self.property_key,
                "observed_value": observed,
                "observed_relative_atomic_mass": observed,
            },
            provenance=(Provenance(
                source_id=f"episteme://executor/{self.method}",
                captured_at=created_at,
                source_location=f"episteme://executor/{self.method}",
                source_version=self.method_version,
                note="Deterministic held-out result for the Phase 29 benchmark.",
            ),),
            created_at=created_at,
        )
        store.put_record(result)
        return result


@dataclass(frozen=True, slots=True)
class RediscoveryPredictionEvaluator:
    """Host-owned deterministic evaluator for the quantitative benchmark."""

    pre_discovery_records: tuple[Record, ...]
    property_key: str = "relative_atomic_mass"
    tolerance: float = 0.05
    method: str = "phase29_rediscovery_evaluation"
    method_version: str = "1"

    def evaluate(
        self, store: Store, result: Record, proposal, predictions: tuple[Prediction, ...],
        *, comparison_conditions: str, created_at: str,
    ) -> tuple[PredictionEvaluation, ...]:
        if result.kind is not RecordKind.RESULT:
            raise ValueError("rediscovery evaluator requires a RESULT record")
        if not 0 < self.tolerance < 1:
            raise ValueError("tolerance must be between 0 and 1")
        if {p.id for p in predictions} != set(proposal.prediction_ids):
            raise ValueError("predictions must exactly match the experiment proposal")
        observed = float(result.payload["observed_value"])
        baseline = derive_adjacent_midpoint(
            self.pre_discovery_records,
            property_key=self.property_key,
        )
        evaluations = []
        for prediction in predictions:
            if prediction.predicted_numeric_value is None:
                raise ValueError("rediscovery prediction requires predicted_numeric_value")
            predicted = float(prediction.predicted_numeric_value)
            baseline_error = abs(baseline - observed) / abs(observed)
            model_error = abs(predicted - observed) / abs(observed)
            matched = model_error <= self.tolerance and model_error <= baseline_error
            if model_error > self.tolerance:
                verdict = "outside_tolerance"
            elif model_error < baseline_error:
                verdict = "beats_baseline"
            elif model_error == baseline_error:
                verdict = "ties_baseline"
            else:
                verdict = "worse_than_baseline"
            outcome = PredictionEvaluationOutcome.CONSISTENT if matched else PredictionEvaluationOutcome.INCONSISTENT
            rationale = (
                "predicted=" + format(predicted, ".6g")
                + "; baseline=" + format(baseline, ".6g")
                + "; baseline_error=" + format(baseline_error, ".6g")
                + "; observed_held_out=" + format(observed, ".6g")
                + "; model_error=" + format(model_error, ".6g")
                + "; tolerance=" + format(self.tolerance, ".6g")
                + "; verdict=" + verdict
            )
            evaluation = PredictionEvaluation(
                id=str(uuid4()),
                result_id=result.id,
                prediction_id=prediction.id,
                experiment_proposal_id=proposal.id,
                comparison_conditions=comparison_conditions,
                assumptions=prediction.assumptions,
                outcome=outcome,
                rationale=rationale,
                method=self.method,
                method_version=self.method_version,
                created_at=created_at,
            )
            store.put_prediction_evaluation(evaluation)
            evaluations.append(evaluation)
        return tuple(evaluations)
