"""Deterministic Phase 4 proposal construction.

These helpers construct generated hypotheses and predictions from explicitly
supplied content. They do not infer scientific meaning, rank alternatives, or
promote generated material to evidence.
"""

from __future__ import annotations

from .model import Hypothesis, Model, Prediction, SCHEMA_VERSION


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


def _new_id() -> str:
    from uuid import uuid4

    return str(uuid4())
