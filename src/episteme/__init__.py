"""Episteme package."""

from .ingest import ingest_jsonl, ingest_jsonl_file
from .model import (
    AssessmentTargetKind,
    DiscoveryFinding,
    DiscoveryFindingKind,
    DiscoveryMeasure,
    EvidenceAssessment,
    LifecycleEvent,
    LifecycleEventKind,
    SCHEMA_VERSION,
    Provenance,
    Record,
    RecordKind,
    Relationship,
    Transformation,
    canonical_json,
    make_record,
    make_relationship,
)
from .discovery import detect_expected_gap, discover_explicit_contradictions, question_from_finding
from .store import Store

__version__ = "0.1.0"

__all__ = [
    "SCHEMA_VERSION",
    "AssessmentTargetKind",
    "DiscoveryFinding",
    "DiscoveryFindingKind",
    "DiscoveryMeasure",
    "EvidenceAssessment",
    "LifecycleEvent",
    "LifecycleEventKind",
    "Provenance",
    "Record",
    "RecordKind",
    "Relationship",
    "Transformation",
    "Store",
    "canonical_json",
    "make_record",
    "make_relationship",
    "detect_expected_gap",
    "discover_explicit_contradictions",
    "question_from_finding",
    "ingest_jsonl",
    "ingest_jsonl_file",
]
