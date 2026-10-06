"""Deterministic evaluation of grounded experiment results.

Evaluation is separate from planning and execution. The evaluator compares a
grounded result against an explicit machine-readable expectation supplied by
the experiment configuration. It never asks an LLM to decide whether a result
supports a prediction.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from .model import (
    ExperimentProposal,
    Prediction,
    PredictionEvaluation,
    PredictionEvaluationOutcome,
    Record,
    RecordKind,
)
from .store import Store


@dataclass(frozen=True, slots=True)
class PositionalPredictionEvaluator:
    """Evaluate whether an expected position was observed.

    expected_presence is the executable meaning of each prediction:
    True means the position should be present; False means it should be
    absent. This explicit configuration is deliberate. Free-form LLM prose
    is not treated as executable scientific semantics.
    """

    position: float
    method: str = "positional_prediction_evaluation"
    method_version: str = "1"

    def evaluate(
        self,
        store: Store,
        result: Record,
        proposal: ExperimentProposal,
        predictions: tuple[Prediction, ...],
        *,
        comparison_conditions: str,
        created_at: str,
    ) -> tuple[PredictionEvaluation, ...]:
        if result.kind is not RecordKind.RESULT:
            raise ValueError("prediction evaluator requires a RESULT record")
        if store.get_record(result.id) is None:
            raise ValueError("prediction evaluator requires a persisted result: " + result.id)
        if store.get_experiment_proposal(proposal.id) is None:
            raise ValueError("prediction evaluator requires a persisted proposal: " + proposal.id)

        proposal_ids = set(proposal.prediction_ids)
        supplied_ids = {prediction.id for prediction in predictions}
        if supplied_ids != proposal_ids:
            raise ValueError("predictions must exactly match the experiment proposal")

        observed = result.payload.get("observed_positions")
        if not isinstance(observed, list) or not all(isinstance(value, (int, float)) for value in observed):
            raise ValueError("result does not contain numeric observed_positions")

        actual_presence = any(float(value) == float(self.position) for value in observed)
        evaluations: list[PredictionEvaluation] = []

        for prediction in predictions:
            expected = prediction.expected_presence
            if expected is None:
                raise ValueError("prediction is missing executable expectation: " + prediction.id)
            if not isinstance(expected, bool):
                raise ValueError("prediction expected_presence must be a boolean")

            if actual_presence == expected:
                outcome = PredictionEvaluationOutcome.CONSISTENT
                rationale = (
                    f"position {self.position!r} was "
                    f"{'present' if actual_presence else 'absent'}, matching the "
                    f"prediction's explicit expectation"
                )
            else:
                outcome = PredictionEvaluationOutcome.INCONSISTENT
                rationale = (
                    f"position {self.position!r} was "
                    f"{'present' if actual_presence else 'absent'}, contradicting the "
                    f"prediction's explicit expectation"
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
