"""Explicit boundary for assessing generated exploration observations.

An assessment references an ExplorationObservation without promoting it to
grounded evidence. Discovery admission remains a separate operation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .model import ExplorationObservation


@dataclass(frozen=True, slots=True)
class ExplorationObservationAssessment:
    """A read-only assessment of generated exploration output."""

    observation_id: str
    accepted: bool
    method: str
    rationale: str

    def __post_init__(self) -> None:
        if not self.observation_id.strip():
            raise ValueError("observation_id must be non-empty")
        if not self.method.strip():
            raise ValueError("method must be non-empty")
        if not self.rationale.strip():
            raise ValueError("rationale must be non-empty")


def assess_exploration_observation(
    store: Any,
    observation_id: str,
    *,
    method: str,
    rationale: str,
    accepted: bool = True,
) -> ExplorationObservationAssessment:
    """Assess an exploration observation without promoting it.

    The observation itself is never modified and is never treated as grounded
    evidence by this function.
    """
    observation = store.get_exploration_observation(observation_id)
    if observation is None:
        raise ValueError("exploration observation does not exist")
    if not isinstance(observation, ExplorationObservation):
        raise ValueError("store returned an invalid exploration observation")

    return ExplorationObservationAssessment(
        observation_id=observation.id,
        accepted=accepted,
        method=method,
        rationale=rationale,
    )
