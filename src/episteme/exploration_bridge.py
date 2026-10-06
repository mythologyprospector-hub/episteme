"""Durable boundary between generated exploration and explicit discovery.

Exploration observations remain generated artifacts. This module provides the
persisted assessment and explicit discovery-admission step without promoting
the observation to grounded evidence.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from .model import (
    DiscoveryFinding,
    DiscoveryFindingKind,
    DiscoveryMeasure,
    ExplorationObservationAssessment,
    Provenance,
)
from .store import Store


BRIDGE_METHOD_VERSION = "1"


def _validate_uuid(value: str, field: str) -> None:
    try:
        UUID(value)
    except (ValueError, AttributeError, TypeError) as exc:
        raise ValueError(f"{field} must be a UUID string") from exc


def assess_exploration_observation(
    store: Store,
    observation_id: str,
    *,
    accepted: bool,
    method: str,
    method_version: str,
    rationale: str,
    provenance: tuple[Provenance, ...],
    assessed_at: str,
) -> ExplorationObservationAssessment:
    """Persist an assessment of a generated exploration observation.

    The assessment never changes the observation and never makes it grounded.
    """
    _validate_uuid(observation_id, "observation_id")
    if store.get_exploration_observation(observation_id) is None:
        raise ValueError(f"exploration observation not found: {observation_id}")

    assessment = ExplorationObservationAssessment(
        id=str(uuid4()),
        observation_id=observation_id,
        accepted=accepted,
        method=method,
        method_version=method_version,
        rationale=rationale,
        provenance=provenance,
        assessed_at=assessed_at,
    )
    store.put_exploration_observation_assessment(assessment)
    return assessment


def admit_exploration_observation(
    store: Store,
    observation_id: str,
    assessment_id: str,
    created_at: str,
) -> DiscoveryFinding:
    """Create an explicit discovery finding from an accepted observation.

    The observation remains generated. Its original grounded inputs remain the
    finding's grounded input IDs, while the generated observation and persisted
    assessment remain explicit context IDs.
    """
    _validate_uuid(observation_id, "observation_id")
    _validate_uuid(assessment_id, "assessment_id")

    observation = store.get_exploration_observation(observation_id)
    if observation is None:
        raise ValueError(f"exploration observation not found: {observation_id}")

    assessment = store.get_exploration_observation_assessment(assessment_id)
    if assessment is None:
        raise ValueError(f"exploration observation assessment not found: {assessment_id}")
    if assessment.observation_id != observation.id:
        raise ValueError("assessment does not reference the supplied exploration observation")
    if not assessment.accepted:
        raise ValueError("rejected exploration observation cannot enter discovery")

    finding = DiscoveryFinding(
        id=str(uuid4()),
        kind=DiscoveryFindingKind.EXPLORATION_OBSERVATION,
        title="Accepted exploration observation entered discovery",
        description=observation.observation,
        input_ids=observation.input_ids,
        context_ids=(observation.id, assessment.id),
        method="exploration-observation-admission",
        method_version=BRIDGE_METHOD_VERSION,
        rationale=(
            "A persisted assessment explicitly admitted this generated observation "
            "to discovery context. The observation remains generated and is not "
            "treated as grounded evidence. Its represented grounded inputs are "
            "kept separate from the generated observation and assessment."
        ),
        measures=(
            DiscoveryMeasure(
                name="input_count",
                value=float(len(observation.input_ids)),
                scale="count",
                basis="number of grounded inputs represented by the generated observation",
            ),
        ),
        created_at=created_at,
    )
    store.put_discovery_finding(finding)
    return finding
