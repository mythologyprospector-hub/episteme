"""Phase 3 discovery methods.

Discovery artifacts remain derived from grounded inputs. This module never
promotes generated findings into grounded records.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from .model import DiscoveryFinding, DiscoveryFindingKind, DiscoveryMeasure
from .store import Store


DISCOVERY_METHOD_VERSION = "1"


def _validate_uuid(value: str, field: str) -> None:
    try:
        UUID(value)
    except (ValueError, AttributeError, TypeError) as exc:
        raise ValueError(f"{field} must be a UUID string") from exc


def _source_ids(store: Store, input_ids: tuple[str, ...]) -> tuple[str, ...]:
    source_ids: set[str] = set()
    for input_id in input_ids:
        record = store.get_record(input_id)
        if record is not None:
            source_ids.update(item.source_id for item in record.provenance)
            continue
        relationship = store.get_relationship(input_id)
        if relationship is not None:
            source_ids.update(item.source_id for item in relationship.provenance)
    return tuple(sorted(source_ids))


def _measures(store: Store, input_ids: tuple[str, ...]) -> tuple[DiscoveryMeasure, ...]:
    source_ids = _source_ids(store, input_ids)
    return (
        DiscoveryMeasure(
            name="input_count",
            value=float(len(input_ids)),
            scale="count",
            basis="number of grounded input identifiers supplied to the discovery method",
        ),
        DiscoveryMeasure(
            name="source_diversity",
            value=float(len(source_ids)),
            scale="distinct source identifiers",
            basis="distinct source_id values across the grounded inputs",
        ),
    )


def discover_explicit_contradictions(
    store: Store,
    created_at: str,
) -> tuple[DiscoveryFinding, ...]:
    """Surface explicit grounded relationships with the contradicts predicate."""

    findings: list[DiscoveryFinding] = []
    for relationship in store.iter_relationships(predicate="contradicts"):
        input_ids = (
            relationship.id,
            relationship.subject_id,
            relationship.object_id,
        )
        findings.append(
            DiscoveryFinding(
                id=str(uuid4()),
                kind=DiscoveryFindingKind.CONTRADICTION,
                title="Explicit contradiction represented",
                description=(
                    f"Relationship {relationship.id} explicitly states that "
                    f"{relationship.subject_id} contradicts {relationship.object_id}."
                ),
                input_ids=input_ids,
                method="explicit-contradiction-discovery",
                method_version=DISCOVERY_METHOD_VERSION,
                rationale=(
                    "The contradiction is surfaced because the grounded substrate "
                    "already contains an explicit contradicts relationship."
                ),
                measures=_measures(store, input_ids),
                created_at=created_at,
            )
        )
    return tuple(findings)


def detect_expected_gap(
    store: Store,
    subject_id: str,
    predicate: str,
    object_id: str,
    created_at: str,
) -> DiscoveryFinding | None:
    """Return a candidate gap for an explicit expected relationship."""

    _validate_uuid(subject_id, "subject_id")
    _validate_uuid(object_id, "object_id")

    if store.get_record(subject_id) is None:
        raise ValueError(f"gap expectation references missing subject record: {subject_id}")
    if store.get_record(object_id) is None:
        raise ValueError(f"gap expectation references missing object record: {object_id}")
    if not predicate.strip():
        raise ValueError("predicate must be a non-empty string")

    for relationship in store.iter_relationships(predicate=predicate):
        if relationship.subject_id == subject_id and relationship.object_id == object_id:
            return None

    input_ids = (subject_id, object_id)
    return DiscoveryFinding(
        id=str(uuid4()),
        kind=DiscoveryFindingKind.GAP,
        title="Expected relationship is not represented",
        description=(
            f"No grounded relationship currently represents "
            f"{subject_id} --{predicate}--> {object_id}."
        ),
        input_ids=input_ids,
        method="expectation-gap-detection",
        method_version=DISCOVERY_METHOD_VERSION,
        rationale=(
            "The finding exists only because an explicit relationship was requested "
            "and the inspected grounded substrate does not contain that relationship."
        ),
        measures=_measures(store, input_ids),
        created_at=created_at,
        expectation=(subject_id, predicate, object_id),
    )


def question_from_finding(
    finding: DiscoveryFinding,
    created_at: str,
) -> DiscoveryFinding:
    """Turn a gap or tension into a bounded unresolved question."""

    if finding.kind not in {
        DiscoveryFindingKind.GAP,
        DiscoveryFindingKind.TENSION,
    }:
        raise ValueError("questions can only be generated from gap or tension findings")

    return DiscoveryFinding(
        id=str(uuid4()),
        kind=DiscoveryFindingKind.UNRESOLVED_QUESTION,
        title="Unresolved question",
        description=f"What evidence would resolve this finding: {finding.title}?",
        input_ids=finding.input_ids,
        method="bounded-question-generation",
        method_version=DISCOVERY_METHOD_VERSION,
        rationale=(
            "The question identifies what remains unresolved without asserting "
            "an answer or treating the generated question as evidence."
        ),
        measures=finding.measures,
        created_at=created_at,
        related_finding_id=finding.id,
        expectation=finding.expectation,
    )


def discover_evaluation_tensions(
    store: Store,
    created_at: str,
) -> tuple[DiscoveryFinding, ...]:
    """Surface differing evaluations of the same prediction under matching context."""

    groups: dict[tuple[str, str, tuple[str, ...]], list[object]] = {}
    for evaluation in store.iter_prediction_evaluations():
        key = (
            evaluation.prediction_id,
            evaluation.comparison_conditions,
            evaluation.assumptions,
        )
        groups.setdefault(key, []).append(evaluation)

    findings: list[DiscoveryFinding] = []
    for key in sorted(groups):
        evaluations = groups[key]
        outcomes = {evaluation.outcome for evaluation in evaluations}
        if len(evaluations) < 2 or len(outcomes) < 2:
            continue

        evaluations = sorted(evaluations, key=lambda item: item.id)
        input_ids = tuple(dict.fromkeys(evaluation.result_id for evaluation in evaluations))
        context_ids = tuple(evaluation.id for evaluation in evaluations)
        findings.append(
            DiscoveryFinding(
                id=str(uuid4()),
                kind=DiscoveryFindingKind.TENSION,
                title="Prediction has differing evaluation outcomes",
                description=(
                    f"Prediction {key[0]} has differing evaluation classifications "
                    "under matching recorded comparison conditions and assumptions."
                ),
                input_ids=input_ids,
                context_ids=context_ids,
                method="evaluation-conflict-discovery",
                method_version=DISCOVERY_METHOD_VERSION,
                rationale=(
                    "The finding is produced only when the same prediction has more "
                    "than one evaluation outcome within an identical recorded "
                    "comparison context. It does not determine which evaluation is "
                    "correct or why the classifications differ."
                ),
                measures=_measures(store, input_ids),
                created_at=created_at,
            )
        )
    return tuple(findings)
