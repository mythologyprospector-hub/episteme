"""Bounded scouting that produces generated exploration observations.

This module reads only explicitly supplied grounded records. It never creates
grounded records or discovery findings.
"""

from __future__ import annotations

import math
from uuid import uuid4

from .model import ExplorationObservation
from .store import Store

SCOUT_METHOD_VERSION = "1"


def scout_positional_records(
    store: Store,
    record_ids: tuple[str, ...],
    position_key: str,
    *,
    max_records: int,
    created_at: str,
) -> ExplorationObservation:
    """Inspect a bounded set of records and persist their numeric positions.

    The scout reports represented values only. It does not infer gaps,
    relationships, candidates, or truth from those values.
    """
    if not record_ids:
        raise ValueError("record_ids must contain at least one record")
    if isinstance(max_records, bool) or not isinstance(max_records, int) or max_records <= 0:
        raise ValueError("max_records must be a positive integer")
    if len(record_ids) > max_records:
        raise ValueError("record_ids exceed the declared max_records")
    if not isinstance(position_key, str) or not position_key.strip():
        raise ValueError("position_key must be a non-empty string")

    inspected: list[tuple[str, float]] = []
    for record_id in record_ids:
        record = store.get_record(record_id)
        if record is None:
            raise ValueError(f"record not found: {record_id}")
        value = record.payload.get(position_key)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
        ):
            raise ValueError(
                f"record {record_id} requires a finite numeric {position_key}"
            )
        inspected.append((record_id, float(value)))

    inspected.sort(key=lambda item: (item[1], item[0]))
    positions = [value for _, value in inspected]
    evidence = tuple(
        f"record {record_id} has represented {position_key}={value!r}"
        for record_id, value in inspected
    )
    observation = ExplorationObservation(
        id=str(uuid4()),
        observation=(
            f"Bounded scout inspected {len(inspected)} supplied records and found "
            f"represented {position_key} positions: {positions!r}."
        ),
        input_ids=tuple(record_ids),
        evidence=evidence,
        method="bounded-positional-scout",
        method_version=SCOUT_METHOD_VERSION,
        uncertainty=(
            "This is generated inspection output. It does not establish a gap, "
            "entity, relationship, or external fact."
        ),
        parameters={
            "record_ids": list(record_ids),
            "position_key": position_key,
            "max_records": max_records,
        },
        created_at=created_at,
    )
    store.put_exploration_observation(observation)
    return observation
