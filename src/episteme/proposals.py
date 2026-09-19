"""Deterministic Phase 4/10 proposal construction.

These helpers construct generated hypotheses, candidate completions, and
predictions from explicitly supplied content. They do not infer scientific
meaning, rank alternatives, or promote generated material to evidence.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .model import ExperimentProposal, Hypothesis, Model, Prediction, SCHEMA_VERSION

if TYPE_CHECKING:
    from .store import Store


def propose_hypothesis(
    *,
    statement: str,
    finding_ids: tuple[str, ...],
    input_ids: tuple[str, ...] = (),
    method: str,
    method_version: str,
    rationale: str,
    assumptions: tuple[str, ...] = (),
    created_at: str,
) -> Hypothesis:
    """Construct a candidate hypothesis from explicitly supplied material."""
    return Hypothesis(
        id=_new_id(),
        statement=statement,
        finding_ids=finding_ids,
        input_ids=input_ids,
        method=method,
        method_version=method_version,
        rationale=rationale,
        assumptions=assumptions,
        created_at=created_at,
        schema_version=SCHEMA_VERSION,
    )


def complete_structural_gap(
    store: "Store",
    *,
    gap_id: str,
    statement: str,
    method: str,
    method_version: str,
    rationale: str,
    assumptions: tuple[str, ...] = (),
    created_at: str,
) -> Hypothesis:
    """Construct a generated candidate downstream of an established gap.

    The gap must already exist and be a GAP finding. Its grounded inputs are
    carried forward as candidate context, but neither the gap nor those inputs
    are modified or promoted by this operation.
    """
    gap = store.get_discovery_finding(gap_id)
    if gap is None:
        if store.get_record(gap_id) is not None or store.get_relationship(gap_id) is not None:
            raise ValueError("candidate completion requires a gap finding: " + gap_id)
        raise ValueError("candidate completion references missing gap: " + gap_id)
    if gap.kind.value != "gap":
        raise ValueError("candidate completion requires a gap finding: " + gap_id)

    return propose_hypothesis(
        statement=statement,
        finding_ids=(gap.id,),
        input_ids=gap.input_ids,
        method=method,
        method_version=method_version,
        rationale=rationale,
        assumptions=assumptions,
        created_at=created_at,
    )


def represent_model(
    *,
    description: str,
    hypothesis_ids: tuple[str, ...] = (),
    input_ids: tuple[str, ...] = (),
    assumptions: tuple[str, ...] = (),
    method: str,
    method_version: str,
    rationale: str,
    created_at: str,
) -> Model:
    """Construct a generated explanatory model from explicitly supplied material."""
    return Model(
        id=_new_id(),
        description=description,
        hypothesis_ids=hypothesis_ids,
        input_ids=input_ids,
        assumptions=assumptions,
        method=method,
        method_version=method_version,
        rationale=rationale,
        created_at=created_at,
        schema_version=SCHEMA_VERSION,
    )


def predict(
    *,
    source_id: str,
    consequence: str,
    conditions: str,
    assumptions: tuple[str, ...] = (),
    method: str,
    method_version: str,
    rationale: str,
    comparison_hypothesis_ids: tuple[str, ...] = (),
    created_at: str,
) -> Prediction:
    """Construct a bounded prediction from an explicitly supplied source."""
    return Prediction(
        id=_new_id(),
        source_id=source_id,
        consequence=consequence,
        conditions=conditions,
        assumptions=assumptions,
        method=method,
        method_version=method_version,
        rationale=rationale,
        comparison_hypothesis_ids=comparison_hypothesis_ids,
        created_at=created_at,
        schema_version=SCHEMA_VERSION,
    )


def propose_experiment(
    *,
    prediction_ids: tuple[str, ...],
    objective: str,
    proposed_observation: str,
    discrimination_basis: str,
    conditions: str,
    assumptions: tuple[str, ...] = (),
    method: str,
    method_version: str,
    rationale: str,
    created_at: str,
) -> ExperimentProposal:
    """Construct an experiment proposal from explicitly supplied content."""
    return ExperimentProposal(
        id=_new_id(),
        prediction_ids=prediction_ids,
        objective=objective,
        proposed_observation=proposed_observation,
        conditions=conditions,
        discrimination_basis=discrimination_basis,
        assumptions=assumptions,
        method=method,
        method_version=method_version,
        rationale=rationale,
        created_at=created_at,
        schema_version=SCHEMA_VERSION,
    )


def _new_id() -> str:
    from uuid import uuid4

    return str(uuid4())
