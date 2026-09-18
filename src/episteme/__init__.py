"""Episteme package."""

from .ingest import ingest_jsonl, ingest_jsonl_file
from .model import (
    SCHEMA_VERSION,
    Provenance,
    Record,
    RecordKind,
    Relationship,
    canonical_json,
    make_record,
    make_relationship,
)
from .store import Store

__version__ = "0.1.0"

__all__ = [
    "SCHEMA_VERSION",
    "Provenance",
    "Record",
    "RecordKind",
    "Relationship",
    "Store",
    "canonical_json",
    "make_record",
    "make_relationship",
    "ingest_jsonl",
    "ingest_jsonl_file",
]
