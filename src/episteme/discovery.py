"""Phase 3 discovery methods.

Discovery artifacts remain derived from grounded inputs. This module never
promotes generated findings into grounded records.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from .model import (
    DiscoveryExpectation,
    DiscoveryExpectationKind,
    DiscoveryFinding,
    DiscoveryFindingKind,
    DiscoveryMeasure,
)
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
        expectation=DiscoveryExpectation(
                kind=DiscoveryExpectationKind.RELATIONSHIP,
                data={
                    "subject_id": subject_id,
                    "predicate": predicate,
                    "object_id": object_id,
                },
            ),
    )



def detect_structural_sequence_gap(
    store: Store,
    ordered_ids: tuple[str, ...],
    predicate: str,
    created_at: str,
) -> DiscoveryFinding | None:
    """Detect the first missing adjacent relationship in an explicit sequence rule.

    The sequence is the structural rule supplied to the method. The method does
    not infer that the ordering is meaningful outside that represented rule.
    """

    if len(ordered_ids) < 2:
        raise ValueError("ordered_ids must contain at least two records")
    if not predicate.strip():
        raise ValueError("predicate must be a non-empty string")
    for record_id in ordered_ids:
        _validate_uuid(record_id, "ordered_id")
        if store.get_record(record_id) is None:
            raise ValueError(f"sequence references missing record: {record_id}")

    for subject_id, object_id in zip(ordered_ids, ordered_ids[1:]):
        if any(
            relationship.subject_id == subject_id
            and relationship.object_id == object_id
            for relationship in store.iter_relationships(predicate=predicate)
        ):
            continue

        input_ids = tuple(ordered_ids)
        return DiscoveryFinding(
            id=str(uuid4()),
            kind=DiscoveryFindingKind.GAP,
            title="Explicit sequence contains an unrepresented relation",
            description=(
                f"The supplied sequence requires {subject_id} --{predicate}--> "
                f"{object_id}, but that grounded relationship is not represented."
            ),
            input_ids=input_ids,
            method="structural-sequence-gap-discovery",
            method_version=DISCOVERY_METHOD_VERSION,
            rationale=(
                "The gap is established by an explicit ordered structure and its "
                "declared adjacency rule. The method does not infer that the "
                "ordering represents external reality or propose an occupant."
            ),
            measures=(
                *_measures(store, input_ids),
                DiscoveryMeasure(
                    name="structural_position_count",
                    value=float(len(ordered_ids) - 1),
                    scale="expected adjacent relations",
                    basis="number of adjacent positions required by the supplied sequence",
                ),
                DiscoveryMeasure(
                    name="missing_position_count",
                    value=1.0,
                    scale="missing adjacent relations",
                    basis="first unrepresented adjacency in the supplied sequence",
                ),
            ),
            created_at=created_at,
            expectation=DiscoveryExpectation(
                kind=DiscoveryExpectationKind.RELATIONSHIP,
                data={
                    "subject_id": subject_id,
                    "predicate": predicate,
                    "object_id": object_id,
                },
            ),
        )

    return None


def detect_structural_payload_sequence_gap(
    store: Store,
    record_ids: tuple[str, ...],
    position_key: str,
    predicate: str,
    created_at: str,
) -> DiscoveryFinding | None:
    """Detect a missing adjacent relation from positions represented in records.

    The ordering rule is derived from a declared record payload field. The
    detector therefore does not receive the expected relationship or its
    ordered endpoints directly; it derives them from grounded records and
    then checks the grounded relationship substrate.
    """

    if len(record_ids) < 2:
        raise ValueError("record_ids must contain at least two records")
    if not position_key.strip():
        raise ValueError("position_key must be a non-empty string")
    if not predicate.strip():
        raise ValueError("predicate must be a non-empty string")

    positioned: list[tuple[float, str]] = []
    seen_positions: set[float] = set()
    for record_id in record_ids:
        _validate_uuid(record_id, "record_id")
        record = store.get_record(record_id)
        if record is None:
            raise ValueError(f"sequence references missing record: {record_id}")
        value = record.payload.get(position_key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(
                f"record {record_id} requires numeric payload field: {position_key}"
            )
        position = float(value)
        if position in seen_positions:
            raise ValueError(f"duplicate structural position: {position}")
        seen_positions.add(position)
        positioned.append((position, record_id))

    positioned.sort()
    ordered_ids = tuple(record_id for _, record_id in positioned)
    relationships = {
        (relationship.subject_id, relationship.object_id)
        for relationship in store.iter_relationships(predicate=predicate)
    }

    for subject_id, object_id in zip(ordered_ids, ordered_ids[1:]):
        if (subject_id, object_id) in relationships:
            continue

        input_ids = tuple(record_ids)
        return DiscoveryFinding(
            id=str(uuid4()),
            kind=DiscoveryFindingKind.GAP,
            title="Grounded positions contain an unrepresented relation",
            description=(
                f"Records ordered by grounded field {position_key!r} require "
                f"{subject_id} --{predicate}--> {object_id}, but that grounded "
                "relationship is not represented."
            ),
            input_ids=input_ids,
            method="structural-payload-sequence-gap-discovery",
            method_version=DISCOVERY_METHOD_VERSION,
            rationale=(
                "The structural ordering is derived from a declared field in the "
                "grounded records. The detector derives the missing adjacency from "
                "that ordering rather than receiving the expected relationship "
                "directly, and it does not propose an occupant or infer external reality."
            ),
            measures=(
                *_measures(store, input_ids),
                DiscoveryMeasure(
                    name="structural_position_count",
                    value=float(len(ordered_ids) - 1),
                    scale="expected adjacent relations",
                    basis="number of adjacent positions after sorting the declared grounded field",
                ),
                DiscoveryMeasure(
                    name="missing_position_count",
                    value=1.0,
                    scale="missing adjacent relations",
                    basis="first unrepresented adjacency derived from grounded positions",
                ),
            ),
            created_at=created_at,
            expectation=DiscoveryExpectation(
                kind=DiscoveryExpectationKind.RELATIONSHIP,
                data={
                    "subject_id": subject_id,
                    "predicate": predicate,
                    "object_id": object_id,
                },
            ),
        )

    return None



def detect_constraint_gap(
    store: Store,
    record_ids: tuple[str, ...],
    value_key: str,
    lower_bound: float,
    upper_bound: float,
    bin_width: float,
    created_at: str,
) -> DiscoveryFinding | None:
    """Detect an unrepresented interior interval under an explicit constraint.

    The caller supplies the bounded state-space constraint and the resolution at
    which occupancy is inspected. A gap is reported only for an empty interior
    interval whose immediately neighboring intervals are both represented by
    grounded observations. The method therefore identifies a bounded vacancy in
    the represented structure without asserting that an external state occupies it.
    """

    if len(record_ids) < 3:
        raise ValueError("record_ids must contain at least three records")
    if not value_key.strip():
        raise ValueError("value_key must be a non-empty string")
    if not math.isfinite(lower_bound) or not math.isfinite(upper_bound):
        raise ValueError("bounds must be finite")
    if upper_bound <= lower_bound:
        raise ValueError("upper_bound must be greater than lower_bound")
    if not math.isfinite(bin_width) or bin_width <= 0:
        raise ValueError("bin_width must be a positive finite number")

    values: list[float] = []
    for record_id in record_ids:
        _validate_uuid(record_id, "record_id")
        record = store.get_record(record_id)
        if record is None:
            raise ValueError(f"constraint references missing record: {record_id}")
        value = record.payload.get(value_key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(
                f"record {record_id} requires numeric payload field: {value_key}"
            )
        numeric = float(value)
        if not math.isfinite(numeric):
            raise ValueError(f"record {record_id} requires a finite numeric value")
        if numeric < lower_bound or numeric > upper_bound:
            raise ValueError(
                f"record {record_id} value violates explicit bounds: {value_key}"
            )
        values.append(numeric)

    interval_count = int(math.ceil((upper_bound - lower_bound) / bin_width))
    occupied: set[int] = set()
    for value in values:
        index = min(
            interval_count - 1,
            int(math.floor((value - lower_bound) / bin_width)),
        )
        occupied.add(index)

    for index in range(1, interval_count - 1):
        if index in occupied or index - 1 not in occupied or index + 1 not in occupied:
            continue

        interval_start = lower_bound + index * bin_width
        interval_end = min(upper_bound, interval_start + bin_width)
        input_ids = tuple(record_ids)
        return DiscoveryFinding(
            id=str(uuid4()),
            kind=DiscoveryFindingKind.GAP,
            title="Bounded constraint region is unrepresented",
            description=(
                f"Grounded {value_key!r} observations satisfy the explicit bounds "
                f"[{lower_bound!r}, {upper_bound!r}] but no observation occupies the "
                f"interior interval [{interval_start!r}, {interval_end!r})."
            ),
            input_ids=input_ids,
            method="bounded-constraint-gap-discovery",
            method_version=DISCOVERY_METHOD_VERSION,
            rationale=(
                "The gap is established by an explicit bounded constraint and "
                "grounded observations on both sides of an empty interior interval. "
                "The detector identifies only a vacancy in the represented state "
                "space; it does not assert that an external state exists there or "
                "propose a candidate occupant."
            ),
            measures=(
                *_measures(store, input_ids),
                DiscoveryMeasure(
                    name="constraint_interval_count",
                    value=float(interval_count),
                    scale="bounded intervals",
                    basis="explicit bounds divided at the declared inspection resolution",
                ),
                DiscoveryMeasure(
                    name="constraint_occupied_interval_count",
                    value=float(len(occupied)),
                    scale="occupied bounded intervals",
                    basis="grounded observations mapped to the declared interval structure",
                ),
                DiscoveryMeasure(
                    name="constraint_missing_interval_count",
                    value=1.0,
                    scale="interior empty intervals with occupied neighbors",
                    basis="first bounded interior interval absent between represented intervals",
                ),
            ),
            created_at=created_at,
            expectation=DiscoveryExpectation(
                kind=DiscoveryExpectationKind.CONSTRAINT,
                data={
                    "constraint": {
                        "value_key": value_key,
                        "lower_bound": lower_bound,
                        "upper_bound": upper_bound,
                        "bin_width": bin_width,
                    },
                    "empty_interval": {
                        "lower_bound": interval_start,
                        "upper_bound": interval_end,
                    },
                },
            ),
        )

    return None


def detect_accounting_gap(
    store: Store,
    total_record_id: str,
    component_record_ids: tuple[str, ...],
    quantity_key: str,
    created_at: str,
) -> DiscoveryFinding | None:
    """Detect an unresolved term in an explicit total-equals-components balance.

    The accounting rule is supplied by this method: the grounded total must equal
    the sum of the grounded component quantities. A non-zero residual establishes
    only an accounting gap in the represented substrate; it does not assert that
    an external quantity or entity corresponding to the residual exists.
    """

    _validate_uuid(total_record_id, "total_record_id")
    if not component_record_ids:
        raise ValueError("component_record_ids must contain at least one record")
    if not quantity_key.strip():
        raise ValueError("quantity_key must be a non-empty string")

    total_record = store.get_record(total_record_id)
    if total_record is None:
        raise ValueError(f"accounting references missing total record: {total_record_id}")

    _validate_uuid(total_record_id, "total_record_id")
    total_value = total_record.payload.get(quantity_key)
    if isinstance(total_value, bool) or not isinstance(total_value, (int, float)):
        raise ValueError(
            f"record {total_record_id} requires numeric payload field: {quantity_key}"
        )

    component_values: list[tuple[str, float]] = []
    for record_id in component_record_ids:
        _validate_uuid(record_id, "component_record_id")
        record = store.get_record(record_id)
        if record is None:
            raise ValueError(f"accounting references missing component record: {record_id}")
        value = record.payload.get(quantity_key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(
                f"record {record_id} requires numeric payload field: {quantity_key}"
            )
        component_values.append((record_id, float(value)))

    total = float(total_value)
    component_sum = sum(value for _, value in component_values)
    residual = total - component_sum

    if residual == 0.0:
        return None

    input_ids = (total_record_id, *component_record_ids)
    return DiscoveryFinding(
        id=str(uuid4()),
        kind=DiscoveryFindingKind.GAP,
        title="Accounting structure contains an unresolved term",
        description=(
            f"The grounded total {total!r} differs from the grounded component "
            f"sum {component_sum!r} by residual {residual!r} for {quantity_key!r}."
        ),
        input_ids=input_ids,
        method="accounting-balance-gap-discovery",
        method_version=DISCOVERY_METHOD_VERSION,
        rationale=(
            "The gap is established by the explicitly declared accounting rule "
            "that the grounded total equals the sum of the supplied grounded "
            "components. The residual is a bounded property of the represented "
            "accounting structure; the method does not assert an external missing "
            "quantity or propose a candidate occupant."
        ),
        measures=(
            *_measures(store, input_ids),
            DiscoveryMeasure(
                name="accounting_residual",
                value=residual,
                scale="quantity units from declared payload field",
                basis="grounded total minus sum of grounded component quantities",
            ),
        ),
        created_at=created_at,
        expectation=DiscoveryExpectation(
            kind=DiscoveryExpectationKind.ACCOUNTING,
            data={
                "quantity": quantity_key,
                "residual": residual,
                "total_record_id": total_record_id,
                "component_record_ids": list(component_record_ids),
            },
        ),
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


def discover_competing_prediction_opportunities(
    store: Store,
    created_at: str,
) -> tuple[DiscoveryFinding, ...]:
    """Surface explicit competing predictions with different consequences."""

    groups: dict[tuple[tuple[str, ...], str, tuple[str, ...]], list[object]] = {}
    for prediction in store.iter_predictions():
        if len(prediction.comparison_hypothesis_ids) < 2:
            continue
        comparison_set = tuple(sorted(set(prediction.comparison_hypothesis_ids)))
        if len(comparison_set) < 2:
            continue
        key = (comparison_set, prediction.conditions, prediction.assumptions)
        groups.setdefault(key, []).append(prediction)

    findings: list[DiscoveryFinding] = []
    for key in sorted(groups):
        predictions = sorted(groups[key], key=lambda item: item.id)
        by_source: dict[str, object] = {}
        for prediction in predictions:
            by_source.setdefault(prediction.source_id, prediction)
        if len(by_source) < 2:
            continue
        consequences = {prediction.consequence for prediction in by_source.values()}
        if len(consequences) < 2:
            continue

        grounded_ids: set[str] = set()
        for hypothesis_id in key[0]:
            hypothesis = store.get_hypothesis(hypothesis_id)
            if hypothesis is None:
                continue
            grounded_ids.update(hypothesis.input_ids)
        input_ids = tuple(sorted(grounded_ids))
        if not input_ids:
            continue

        context_ids = tuple(prediction.id for prediction in by_source.values())
        findings.append(
            DiscoveryFinding(
                id=str(uuid4()),
                kind=DiscoveryFindingKind.TENSION,
                title="Competing hypotheses make distinguishable predictions",
                description=(
                    "Represented competing hypotheses specify different predicted "
                    "consequences under matching conditions and assumptions."
                ),
                input_ids=input_ids,
                context_ids=context_ids,
                method="competing-prediction-discovery",
                method_version=DISCOVERY_METHOD_VERSION,
                rationale=(
                    "The finding is produced only when multiple explicitly compared "
                    "hypotheses have predictions under the same conditions and "
                    "assumptions with distinct consequences. It does not rank the "
                    "hypotheses or assert that any consequence is true."
                ),
                measures=_measures(store, input_ids),
                created_at=created_at,
            )
        )
    return tuple(findings)
