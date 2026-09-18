"""Biology domain adapter for Episteme."""

from __future__ import annotations

from typing import Any, Mapping

from ..model import Provenance, Record, RecordKind, canonical_json, make_record

BIOLOGY_DOMAIN = "biology"
BIOLOGY_SCHEMA = "biology-observation-v1"
_VALID_STATUSES = {"observed", "not_observed", "not_reported", "unresolved"}


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def validate_observation(payload: Mapping[str, Any]) -> None:
    """Validate biological observation structure without interpreting it."""
    if not isinstance(payload, Mapping):
        raise ValueError("biology observation must be a mapping")

    observation = payload.get("observation")
    if not isinstance(observation, Mapping):
        raise ValueError("biology observation must be a mapping")

    status = payload.get("status", "observed")
    if not isinstance(status, str) or status not in _VALID_STATUSES:
        raise ValueError(f"unsupported biology observation status: {status}")

    if status == "observed":
        if not observation:
            raise ValueError("observed biology observation must contain data")
    elif observation:
        raise ValueError("non-observed biology status must not carry observation data")

    for field in ("subject", "trial"):
        if field in payload:
            _require_text(payload[field], field)

    conditions = payload.get("conditions")
    if conditions is not None and not isinstance(conditions, Mapping):
        raise ValueError("conditions must be a mapping")

    canonical_json(dict(payload))


def make_biology_observation(
    payload: Mapping[str, Any],
    provenance: tuple[Provenance, ...],
    created_at: str,
) -> Record:
    """Translate a validated biological observation into a normal Episteme record."""
    validate_observation(payload)
    domain_payload = {
        "domain": BIOLOGY_DOMAIN,
        "schema": BIOLOGY_SCHEMA,
        "data": dict(payload),
    }
    return make_record(
        kind=RecordKind.OBSERVATION,
        payload=domain_payload,
        provenance=provenance,
        created_at=created_at,
    )
