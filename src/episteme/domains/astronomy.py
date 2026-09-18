"""Astronomy domain adapter for Episteme."""

from __future__ import annotations

import math
from typing import Any, Mapping

from ..model import Provenance, Record, RecordKind, canonical_json, make_record

ASTRONOMY_DOMAIN = "astronomy"
ASTRONOMY_SCHEMA = "astronomy-measurement-v1"
_VALID_STATUSES = {"measured", "not_measured", "not_reported", "uncertain"}


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def validate_measurement(payload: Mapping[str, Any]) -> None:
    """Validate astronomy-specific measurement structure without interpreting it."""
    if not isinstance(payload, Mapping):
        raise ValueError("astronomy measurement must be a mapping")

    quantity = _require_text(payload.get("quantity"), "quantity")
    _ = quantity

    status = payload.get("status", "measured")
    if not isinstance(status, str):
        raise ValueError("astronomy measurement status must be a string")
    if status not in _VALID_STATUSES:
        raise ValueError(f"unsupported astronomy measurement status: {status}")

    if status == "measured":
        value = payload.get("value")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("measured astronomy value must be numeric")
        if not math.isfinite(float(value)):
            raise ValueError("measured astronomy value must be finite")
        _require_text(payload.get("unit"), "unit")
    elif "value" in payload or "unit" in payload:
        raise ValueError("non-measured astronomy status must not carry value or unit")

    if "uncertainty" in payload:
        canonical_json(payload["uncertainty"])

    if "target" in payload:
        _require_text(payload["target"], "target")
    if "instrument" in payload:
        _require_text(payload["instrument"], "instrument")
    if "observed_at" in payload:
        _require_text(payload["observed_at"], "observed_at")

    conditions = payload.get("conditions")
    if conditions is not None:
        if not isinstance(conditions, Mapping):
            raise ValueError("conditions must be a mapping")
        for key in conditions:
            _require_text(key, "condition name")

    canonical_json(dict(payload))


def make_astronomy_measurement(
    payload: Mapping[str, Any],
    provenance: tuple[Provenance, ...],
    created_at: str,
) -> Record:
    """Translate a validated astronomy measurement into a normal Episteme record."""
    validate_measurement(payload)
    domain_payload = {
        "domain": ASTRONOMY_DOMAIN,
        "schema": ASTRONOMY_SCHEMA,
        "data": dict(payload),
    }
    return make_record(
        kind=RecordKind.MEASUREMENT,
        payload=domain_payload,
        provenance=provenance,
        created_at=created_at,
    )
