"""Safe public-source import adapters."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .model import Provenance, Record, RecordKind
from .store import Store


CROSSREF_ADAPTER = "crossref-work-metadata"
CROSSREF_ADAPTER_VERSION = "1"
CROSSREF_SOURCE_ID = "crossref"


def import_crossref_works(
    data: Mapping[str, Any],
    store: Store,
    *,
    captured_at: str,
    source_location: str | None = None,
    capture_id: str | None = None,
) -> int:
    """Import Crossref work metadata as grounded source records.

    The adapter preserves the supplied Crossref work object as payload. It does
    not extract scientific claims or infer epistemic status from the metadata.
    """
    if capture_id is not None:
        if store.get_captured_representation(capture_id) is None:
            raise ValueError(f"Crossref import references missing capture: {capture_id}")

    if not isinstance(data, Mapping):
        raise ValueError("Crossref response must be a mapping")

    message = data.get("message")
    if not isinstance(message, Mapping):
        raise ValueError("Crossref response requires a message object")

    items = message.get("items")
    if not isinstance(items, list):
        raise ValueError("Crossref response requires a message.items list")

    records: list[Record] = []
    for index, item in enumerate(items):
        if not isinstance(item, Mapping):
            raise ValueError(f"Crossref item {index} must be an object")

        doi = item.get("DOI")
        if not isinstance(doi, str) or not doi.strip():
            raise ValueError(f"Crossref item {index} requires a DOI")

        location = source_location or f"https://doi.org/{doi}"
        provenance = (
            Provenance(
                source_id=f"{CROSSREF_SOURCE_ID}:{doi}",
                source_location=location,
                source_version=_source_version(item),
                captured_at=captured_at,
                capture_id=capture_id,
                note=f"Imported by {CROSSREF_ADAPTER} v{CROSSREF_ADAPTER_VERSION}",
            ),
        )

        records.append(Record(
            id=_record_id(doi),
            kind=RecordKind.SOURCE,
            payload={
                "external_format": "crossref-work",
                "adapter": CROSSREF_ADAPTER,
                "adapter_version": CROSSREF_ADAPTER_VERSION,
                "work": dict(item),
            },
            provenance=provenance,
            created_at=captured_at,
        ))

    for record in records:
        store.put_record(record)

    return len(records)


def _source_version(item: Mapping[str, Any]) -> str | None:
    for key in ("created", "published-online", "published-print", "issued"):
        value = item.get(key)
        if isinstance(value, Mapping):
            date_parts = value.get("date-parts")
            if isinstance(date_parts, list) and date_parts:
                return str(date_parts[0])
    return None


def _record_id(doi: str) -> str:
    import uuid

    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"https://doi.org/{doi.strip().lower()}"))
