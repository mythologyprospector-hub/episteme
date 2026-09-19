"""Phase 9 proof of structural-gap discovery."""

from episteme import (
    DiscoveryExpectation,
    DiscoveryExpectationKind,
    DiscoveryFindingKind,
    Provenance,
    Record,
    RecordKind,
    Store,
    detect_accounting_gap,
    detect_constraint_gap,
    detect_structural_sequence_gap,
    detect_structural_payload_sequence_gap,
    make_relationship,
)

CREATED = "2026-09-19T00:00:00Z"
PROVENANCE = (
    Provenance(
        source_id="phase9-structural-fixture",
        captured_at=CREATED,
        source_location="https://example.org/phase9",
        source_version="1",
    ),
)


def test_structural_sequence_gap_requires_explicit_structure():
    records = tuple(
        Record(
            id=f"{index:08d}-0000-4000-8000-000000000000",
            kind=RecordKind.OBSERVATION,
            payload={"position": index},
            provenance=PROVENANCE,
            created_at=CREATED,
        )
        for index in range(1, 4)
    )

    with Store() as store:
        for record in records:
            store.put_record(record)

        relationship = make_relationship(
            subject_id=records[0].id,
            predicate="next",
            object_id=records[1].id,
            provenance=PROVENANCE,
            created_at=CREATED,
        )
        store.put_relationship(relationship)

        gap = detect_structural_sequence_gap(
            store,
            ordered_ids=tuple(record.id for record in records),
            predicate="next",
            created_at="2026-09-19T00:01:00Z",
        )

    assert gap is not None
    assert gap.kind is DiscoveryFindingKind.GAP
    assert gap.input_ids == tuple(record.id for record in records)
    assert gap.expectation == DiscoveryExpectation(
        kind=DiscoveryExpectationKind.RELATIONSHIP,
        data={
            "subject_id": records[1].id,
            "predicate": "next",
            "object_id": records[2].id,
        },
    )
    assert gap.context_ids == ()
    assert "explicit ordered structure" in gap.rationale



def test_structural_payload_sequence_gap_derives_expectation_from_grounded_records():
    records = tuple(
        Record(
            id=f"{index:08d}-0000-4000-8000-000000000000",
            kind=RecordKind.OBSERVATION,
            payload={"position": index},
            provenance=PROVENANCE,
            created_at=CREATED,
        )
        for index in range(1, 4)
    )

    with Store() as store:
        for record in records:
            store.put_record(record)

        store.put_relationship(
            make_relationship(
                subject_id=records[0].id,
                predicate="next",
                object_id=records[1].id,
                provenance=PROVENANCE,
                created_at=CREATED,
            )
        )

        gap = detect_structural_payload_sequence_gap(
            store,
            record_ids=tuple(record.id for record in records),
            position_key="position",
            predicate="next",
            created_at="2026-09-19T00:02:00Z",
        )

    assert gap is not None
    assert gap.kind is DiscoveryFindingKind.GAP
    assert gap.expectation == DiscoveryExpectation(
        kind=DiscoveryExpectationKind.RELATIONSHIP,
        data={
            "subject_id": records[1].id,
            "predicate": "next",
            "object_id": records[2].id,
        },
    )
    assert "grounded records" in gap.rationale



def test_structural_payload_sequence_gap_ignores_input_order():
    records = tuple(
        Record(
            id=f"{index:08d}-0000-4000-8000-000000000000",
            kind=RecordKind.OBSERVATION,
            payload={"position": index},
            provenance=PROVENANCE,
            created_at=CREATED,
        )
        for index in range(1, 4)
    )

    with Store() as store:
        for record in records:
            store.put_record(record)
        store.put_relationship(
            make_relationship(
                subject_id=records[0].id,
                predicate="next",
                object_id=records[1].id,
                provenance=PROVENANCE,
                created_at=CREATED,
            )
        )

        gap = detect_structural_payload_sequence_gap(
            store,
            record_ids=(records[2].id, records[0].id, records[1].id),
            position_key="position",
            predicate="next",
            created_at="2026-09-19T00:03:00Z",
        )

    assert gap is not None
    assert gap.expectation == DiscoveryExpectation(
        kind=DiscoveryExpectationKind.RELATIONSHIP,
        data={
            "subject_id": records[1].id,
            "predicate": "next",
            "object_id": records[2].id,
        },
    )


def test_discovery_expectation_supports_non_relationship_structures():
    positional = DiscoveryExpectation(
        kind=DiscoveryExpectationKind.POSITIONAL,
        data={"position": 4},
    )
    constraint = DiscoveryExpectation(
        kind=DiscoveryExpectationKind.CONSTRAINT,
        data={"constraint": "mass must be conserved"},
    )
    accounting = DiscoveryExpectation(
        kind=DiscoveryExpectationKind.ACCOUNTING,
        data={"quantity": "unaccounted mass"},
    )

    assert DiscoveryExpectation.from_dict(positional.to_dict()) == positional
    assert DiscoveryExpectation.from_dict(constraint.to_dict()) == constraint
    assert DiscoveryExpectation.from_dict(accounting.to_dict()) == accounting


def test_accounting_gap_exposes_grounded_residual_without_proposing_occupant():
    total = Record(
        id="44444444-4444-4444-8444-444444444444",
        kind=RecordKind.MEASUREMENT,
        payload={"mass": 10.0},
        provenance=PROVENANCE,
        created_at=CREATED,
    )
    first = Record(
        id="55555555-5555-4555-8555-555555555555",
        kind=RecordKind.MEASUREMENT,
        payload={"mass": 3.0},
        provenance=PROVENANCE,
        created_at=CREATED,
    )
    second = Record(
        id="66666666-6666-4666-8666-666666666666",
        kind=RecordKind.MEASUREMENT,
        payload={"mass": 4.0},
        provenance=PROVENANCE,
        created_at=CREATED,
    )

    with Store() as store:
        for record in (total, first, second):
            store.put_record(record)

        gap = detect_accounting_gap(
            store,
            total_record_id=total.id,
            component_record_ids=(first.id, second.id),
            quantity_key="mass",
            created_at="2026-09-19T00:04:00Z",
        )

    assert gap is not None
    assert gap.kind is DiscoveryFindingKind.GAP
    assert gap.input_ids == (total.id, first.id, second.id)
    assert gap.expectation == DiscoveryExpectation(
        kind=DiscoveryExpectationKind.ACCOUNTING,
        data={
            "quantity": "mass",
            "residual": 3.0,
            "total_record_id": total.id,
            "component_record_ids": [first.id, second.id],
        },
    )
    assert "accounting rule" in gap.rationale
    assert "does not assert an external missing" in gap.rationale



def test_constraint_gap_requires_bounded_constraint_and_occupied_neighbors():
    records = tuple(
        Record(
            id=f"7777777{index}-7777-4777-8777-777777777777",
            kind=RecordKind.MEASUREMENT,
            payload={"temperature": value},
            provenance=PROVENANCE,
            created_at=CREATED,
        )
        for index, value in enumerate((10.0, 20.0, 40.0, 50.0), start=1)
    )

    with Store() as store:
        for record in records:
            store.put_record(record)

        gap = detect_constraint_gap(
            store,
            record_ids=tuple(record.id for record in records),
            value_key="temperature",
            lower_bound=0.0,
            upper_bound=60.0,
            bin_width=10.0,
            created_at="2026-09-19T00:05:00Z",
        )

    assert gap is not None
    assert gap.kind is DiscoveryFindingKind.GAP
    assert gap.input_ids == tuple(record.id for record in records)
    assert gap.expectation == DiscoveryExpectation(
        kind=DiscoveryExpectationKind.CONSTRAINT,
        data={
            "constraint": "temperature is bounded to [0.0, 60.0] with inspection width 10.0",
            "constraint_parameters": {
                "value_key": "temperature",
                "lower_bound": 0.0,
                "upper_bound": 60.0,
                "bin_width": 10.0,
            },
            "empty_interval": {
                "lower_bound": 30.0,
                "upper_bound": 40.0,
            },
        },
    )
    assert "explicit bounded constraint" in gap.rationale
    assert "does not assert that an external state exists" in gap.rationale


def test_constraint_gap_does_not_call_boundary_sparsity_a_hole():
    records = tuple(
        Record(
            id=f"8888888{index}-8888-4888-8888-888888888888",
            kind=RecordKind.MEASUREMENT,
            payload={"temperature": value},
            provenance=PROVENANCE,
            created_at=CREATED,
        )
        for index, value in enumerate((10.0, 20.0, 30.0), start=1)
    )

    with Store() as store:
        for record in records:
            store.put_record(record)

        gap = detect_constraint_gap(
            store,
            record_ids=tuple(record.id for record in records),
            value_key="temperature",
            lower_bound=0.0,
            upper_bound=40.0,
            bin_width=10.0,
            created_at="2026-09-19T00:06:00Z",
        )

    assert gap is None



def test_structural_gap_methods_remain_domain_agnostic_and_deterministic():
    """Different structural forms share the same core discovery boundary."""
    total = Record(
        id="99999991-9999-4999-8999-999999999999",
        kind=RecordKind.MEASUREMENT,
        payload={"mass": 10.0},
        provenance=PROVENANCE,
        created_at=CREATED,
    )
    component_a = Record(
        id="99999992-9999-4999-8999-999999999999",
        kind=RecordKind.MEASUREMENT,
        payload={"mass": 3.0},
        provenance=PROVENANCE,
        created_at=CREATED,
    )
    component_b = Record(
        id="99999993-9999-4999-8999-999999999999",
        kind=RecordKind.MEASUREMENT,
        payload={"mass": 4.0},
        provenance=PROVENANCE,
        created_at=CREATED,
    )
    observations = tuple(
        Record(
            id=f"9999999{index}-9999-4999-8999-999999999999",
            kind=RecordKind.OBSERVATION,
            payload={"position": position},
            provenance=PROVENANCE,
            created_at=CREATED,
        )
        for index, position in enumerate((10, 20, 40, 50), start=4)
    )

    with Store() as store:
        for record in (total, component_a, component_b, *observations):
            store.put_record(record)
        accounting = detect_accounting_gap(
            store,
            total_record_id=total.id,
            component_record_ids=(component_a.id, component_b.id),
            quantity_key="mass",
            created_at="2026-09-19T00:07:00Z",
        )
        constraint = detect_constraint_gap(
            store,
            record_ids=tuple(record.id for record in observations),
            value_key="position",
            lower_bound=0.0,
            upper_bound=60.0,
            bin_width=10.0,
            created_at="2026-09-19T00:08:00Z",
        )

    assert accounting is not None
    assert constraint is not None
    assert accounting.kind is DiscoveryFindingKind.GAP
    assert constraint.kind is DiscoveryFindingKind.GAP
    assert accounting.input_ids == (total.id, component_a.id, component_b.id)
    assert constraint.input_ids == tuple(record.id for record in observations)
    assert accounting.expectation is not None
    assert constraint.expectation is not None
    assert accounting.expectation.kind is DiscoveryExpectationKind.ACCOUNTING
    assert constraint.expectation.kind is DiscoveryExpectationKind.CONSTRAINT
    assert "does not assert" in accounting.rationale
    assert "does not assert" in constraint.rationale

    accounting_copy = accounting.to_dict()
    constraint_copy = constraint.to_dict()
    assert DiscoveryExpectation.from_dict(accounting_copy["expectation"]) == accounting.expectation
    assert DiscoveryExpectation.from_dict(constraint_copy["expectation"]) == constraint.expectation
