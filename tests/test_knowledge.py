from episteme import (
    DiscoveryExpectation,
    DiscoveryExpectationKind,
    Provenance,
    RecordKind,
    Store,
    canonical_json,
    make_record,
    make_relationship,
)


def provenance() -> Provenance:
    return Provenance(
        source_id="source:example",
        source_location="https://example.test/source",
        source_version="1",
        captured_at="2026-09-18T00:00:00Z",
    )


def test_record_requires_provenance():
    try:
        make_record(
            RecordKind.OBSERVATION,
            {"value": 42},
            (),
            "2026-09-18T00:00:00Z",
        )
    except ValueError as exc:
        assert "provenance" in str(exc)
    else:
        raise AssertionError("record without provenance was accepted")


def test_canonical_json_is_deterministic():
    assert canonical_json({"b": 2, "a": 1}) == '{"a":1,"b":2}'


def test_provenance_requires_timezone_aware_timestamp():
    from episteme import Provenance

    for captured_at in ("2026-09-18T00:00:00", "not-a-timestamp"):
        try:
            Provenance(
                source_id="source:example",
                captured_at=captured_at,
            )
        except ValueError as exc:
            assert "captured_at" in str(exc)
        else:
            raise AssertionError("invalid provenance timestamp was accepted")


def test_provenance_source_location_must_be_absolute_uri():
    from episteme import Provenance

    try:
        Provenance(
            source_id="source:example",
            source_location="relative/path",
            captured_at="2026-09-18T00:00:00Z",
        )
    except ValueError as exc:
        assert "source_location" in str(exc)
    else:
        raise AssertionError("relative source location was accepted")


def test_provenance_optional_fields_cannot_be_empty():
    from episteme import Provenance

    for field, kwargs in (
        ("source_version", {"source_version": ""}),
        ("note", {"note": ""}),
    ):
        try:
            Provenance(
                source_id="source:example",
                captured_at="2026-09-18T00:00:00Z",
                **kwargs,
            )
        except ValueError as exc:
            assert field in str(exc)
        else:
            raise AssertionError(f"empty {field} was accepted")


def test_provenance_accepts_non_url_absolute_uri():
    entry = Provenance(
        source_id="source:example",
        source_location="urn:example:source",
        captured_at="2026-09-18T00:00:00Z",
    )

    assert entry.source_location == "urn:example:source"


def test_store_round_trip_for_record():
    record = make_record(
        RecordKind.OBSERVATION,
        {"value": 42, "unit": "arbitrary"},
        (provenance(),),
        "2026-09-18T00:00:01Z",
    )

    with Store() as store:
        store.put_record(record)
        restored = store.get_record(record.id)

    assert restored == record


def test_store_round_trip_for_relationship():
    first = make_record(
        RecordKind.OBSERVATION,
        {"value": 1},
        (provenance(),),
        "2026-09-18T00:00:01Z",
    )
    second = make_record(
        RecordKind.OBSERVATION,
        {"value": 2},
        (provenance(),),
        "2026-09-18T00:00:02Z",
    )

    with Store() as store:
        store.put_record(first)
        store.put_record(second)
        relationship = make_relationship(
            first.id,
            "precedes",
            second.id,
            (provenance(),),
            "2026-09-18T00:00:03Z",
        )
        store.put_relationship(relationship)
        restored = store.get_relationship(relationship.id)

    assert restored == relationship


def test_relationship_cannot_reference_missing_record():
    first = make_record(
        RecordKind.OBSERVATION,
        {"value": 1},
        (provenance(),),
        "2026-09-18T00:00:01Z",
    )

    relationship = make_relationship(
        first.id,
        "precedes",
        "00000000-0000-0000-0000-000000000000",
        (provenance(),),
        "2026-09-18T00:00:02Z",
    )

    with Store() as store:
        store.put_record(first)
        try:
            store.put_relationship(relationship)
        except ValueError as exc:
            assert "missing object" in str(exc)
        else:
            raise AssertionError("dangling relationship was accepted")


def test_identical_payloads_keep_distinct_identity():
    first = make_record(
        RecordKind.OBSERVATION,
        {"value": 42},
        (provenance(),),
        "2026-09-18T00:00:01Z",
    )
    second = make_record(
        RecordKind.OBSERVATION,
        {"value": 42},
        (provenance(),),
        "2026-09-18T00:00:02Z",
    )

    assert first.id != second.id



def test_jsonl_ingestion_preserves_grounded_records(tmp_path):
    from episteme import ingest_jsonl_file

    fixture = tmp_path / "sample.jsonl"
    fixture.write_text(
        '{"id":"11111111-1111-4111-8111-111111111111","kind":"observation","payload":{"value":42},"provenance":[{"source_id":"example:source","captured_at":"2026-09-18T00:00:00Z"}],"created_at":"2026-09-18T00:00:00Z","schema_version":1}\n',
        encoding="utf-8",
    )

    with Store() as store:
        assert ingest_jsonl_file(fixture, store) == 1
        record = store.get_record("11111111-1111-4111-8111-111111111111")

    assert record is not None
    assert record.kind is RecordKind.OBSERVATION
    assert record.payload["value"] == 42


def test_jsonl_ingestion_validates_entire_batch_before_persistence(tmp_path):
    from episteme import ingest_jsonl_file

    fixture = tmp_path / "mixed.jsonl"
    fixture.write_text(
        '{"id":"aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa","kind":"observation","payload":{"value":42},"provenance":[{"source_id":"example:source","captured_at":"2026-09-18T00:00:00Z"}],"created_at":"2026-09-18T00:00:00Z","schema_version":1}\n'
        '{"kind":"observation"}\n',
        encoding="utf-8",
    )

    with Store() as store:
        try:
            ingest_jsonl_file(fixture, store)
        except ValueError as exc:
            assert "line 2" in str(exc)
        else:
            raise AssertionError("invalid batch was accepted")

        assert list(store.iter_records()) == []


def test_jsonl_ingestion_rejects_malformed_record(tmp_path):
    from episteme import ingest_jsonl_file

    fixture = tmp_path / "bad.jsonl"
    fixture.write_text('{"kind":"observation"}\n', encoding="utf-8")

    with Store() as store:
        try:
            ingest_jsonl_file(fixture, store)
        except ValueError as exc:
            assert "line 1" in str(exc)
        else:
            raise AssertionError("malformed record was accepted")



def test_bipm_fixture_ingests_end_to_end():
    from pathlib import Path
    from episteme import ingest_jsonl_file

    fixture = Path(__file__).parent / "fixtures" / "bipm_si_sample.jsonl"

    with Store() as store:
        assert ingest_jsonl_file(fixture, store) == 2
        records = list(store.iter_records())

    assert [record.kind for record in records] == [RecordKind.SOURCE, RecordKind.MEASUREMENT]
    assert records[1].payload["value"] == 299792458
    assert records[1].provenance[0].source_id == "bipm:si-metre"



def test_lifecycle_history_is_append_only():
    from episteme import LifecycleEvent, LifecycleEventKind

    record = make_record(
        RecordKind.OBSERVATION,
        {"value": 42},
        (provenance(),),
        "2026-09-18T00:00:00Z",
    )
    replacement = make_record(
        RecordKind.OBSERVATION,
        {"value": 43},
        (provenance(),),
        "2026-09-18T00:00:01Z",
    )
    event = LifecycleEvent(
        id="22222222-2222-4222-8222-222222222222",
        record_id=record.id,
        kind=LifecycleEventKind.SUPERSEDED,
        occurred_at="2026-09-18T00:00:02Z",
        replacement_record_id=replacement.id,
        reason="Corrected source value",
        provenance=(provenance(),),
    )

    with Store() as store:
        store.put_record(record)
        store.put_record(replacement)
        store.put_lifecycle_event(event)
        history = list(store.iter_lifecycle_events(record.id))

    assert history == [event]
    assert history[0].replacement_record_id == replacement.id


def test_retracted_event_requires_reason():
    from episteme import LifecycleEvent, LifecycleEventKind

    try:
        LifecycleEvent(
            id="33333333-3333-4333-8333-333333333333",
            record_id="44444444-4444-4444-8444-444444444444",
            kind=LifecycleEventKind.RETRACTED,
            occurred_at="2026-09-18T00:00:00Z",
            provenance=(provenance(),),
        )
    except ValueError as exc:
        assert "reason" in str(exc)
    else:
        raise AssertionError("retracted event without reason was accepted")


def test_evidence_assessment_is_contextual_and_persistent():
    from episteme import AssessmentTargetKind, EvidenceAssessment

    record = make_record(
        RecordKind.OBSERVATION,
        {"value": 42},
        (provenance(),),
        "2026-09-18T00:00:00Z",
    )
    assessment = EvidenceAssessment(
        id="55555555-5555-4555-8555-555555555555",
        target_kind=AssessmentTargetKind.RECORD,
        target_id=record.id,
        method="source-review",
        basis="primary-source inspection",
        rationale="The source directly states the observation.",
        provenance=(provenance(),),
        assessed_at="2026-09-18T00:00:02Z",
    )

    with Store() as store:
        store.put_record(record)
        store.put_evidence_assessment(assessment)
        restored = store.get_evidence_assessment(assessment.id)

    assert restored == assessment


def test_transformation_requires_existing_inputs_and_outputs():
    from episteme import Transformation

    first = make_record(
        RecordKind.OBSERVATION,
        {"value": 1},
        (provenance(),),
        "2026-09-18T00:00:00Z",
    )
    second = make_record(
        RecordKind.RESULT,
        {"value": 2},
        (provenance(),),
        "2026-09-18T00:00:01Z",
    )
    transformation = Transformation(
        id="66666666-6666-4666-8666-666666666666",
        input_ids=(first.id,),
        operation="example-transform",
        operation_version="1",
        assumptions=("example input is valid",),
        output_ids=(second.id,),
        executed_at="2026-09-18T00:00:02Z",
        validation_result="verified",
        provenance=(provenance(),),
    )

    with Store() as store:
        store.put_record(first)
        try:
            store.put_transformation(transformation)
        except ValueError as exc:
            assert second.id in str(exc)
        else:
            raise AssertionError("transformation with missing output was accepted")

        store.put_record(second)
        store.put_transformation(transformation)
        assert store.get_transformation(transformation.id) == transformation



def test_discovery_explicit_contradiction_is_traceable_and_persistent():
    from episteme import (
        DiscoveryFindingKind,
        discover_explicit_contradictions,
    )

    first = make_record(
        RecordKind.OBSERVATION,
        {"value": 1},
        (provenance(),),
        "2026-09-18T00:00:00Z",
    )
    second = make_record(
        RecordKind.OBSERVATION,
        {"value": 2},
        (provenance(),),
        "2026-09-18T00:00:01Z",
    )
    contradiction = make_relationship(
        first.id,
        "contradicts",
        second.id,
        (provenance(),),
        "2026-09-18T00:00:02Z",
    )

    with Store() as store:
        store.put_record(first)
        store.put_record(second)
        store.put_relationship(contradiction)

        findings = discover_explicit_contradictions(
            store,
            "2026-09-18T00:00:03Z",
        )
        assert len(findings) == 1
        finding = findings[0]
        assert finding.kind is DiscoveryFindingKind.CONTRADICTION
        assert contradiction.id in finding.input_ids
        assert first.id in finding.input_ids
        assert second.id in finding.input_ids

        store.put_discovery_finding(finding)
        restored = store.get_discovery_finding(finding.id)

    assert restored == finding


def test_discovery_gap_requires_explicit_expectation():
    from episteme import DiscoveryFindingKind, detect_expected_gap

    first = make_record(
        RecordKind.OBSERVATION,
        {"name": "A"},
        (provenance(),),
        "2026-09-18T00:00:00Z",
    )
    second = make_record(
        RecordKind.OBSERVATION,
        {"name": "B"},
        (provenance(),),
        "2026-09-18T00:00:01Z",
    )

    with Store() as store:
        store.put_record(first)
        store.put_record(second)

        finding = detect_expected_gap(
            store,
            first.id,
            "related_to",
            second.id,
            "2026-09-18T00:00:02Z",
        )

    assert finding is not None
    assert finding.kind is DiscoveryFindingKind.GAP
    assert finding.input_ids == (first.id, second.id)
    assert finding.expectation == DiscoveryExpectation(
        kind=DiscoveryExpectationKind.RELATIONSHIP,
        data={
            "subject_id": first.id,
            "predicate": "related_to",
            "object_id": second.id,
        },
    )


def test_discovery_gap_disappears_when_expected_relationship_exists():
    from episteme import detect_expected_gap

    first = make_record(
        RecordKind.OBSERVATION,
        {"name": "A"},
        (provenance(),),
        "2026-09-18T00:00:00Z",
    )
    second = make_record(
        RecordKind.OBSERVATION,
        {"name": "B"},
        (provenance(),),
        "2026-09-18T00:00:01Z",
    )
    relationship = make_relationship(
        first.id,
        "related_to",
        second.id,
        (provenance(),),
        "2026-09-18T00:00:02Z",
    )

    with Store() as store:
        store.put_record(first)
        store.put_record(second)
        store.put_relationship(relationship)

        assert (
            detect_expected_gap(
                store,
                first.id,
                "related_to",
                second.id,
                "2026-09-18T00:00:03Z",
            )
            is None
        )


def test_unresolved_question_preserves_grounded_inputs():
    from episteme import (
        DiscoveryFindingKind,
        detect_expected_gap,
        question_from_finding,
    )

    first = make_record(
        RecordKind.OBSERVATION,
        {"name": "A"},
        (provenance(),),
        "2026-09-18T00:00:00Z",
    )
    second = make_record(
        RecordKind.OBSERVATION,
        {"name": "B"},
        (provenance(),),
        "2026-09-18T00:00:01Z",
    )

    with Store() as store:
        store.put_record(first)
        store.put_record(second)
        gap = detect_expected_gap(
            store,
            first.id,
            "related_to",
            second.id,
            "2026-09-18T00:00:02Z",
        )
        assert gap is not None

    question = question_from_finding(gap, "2026-09-18T00:00:03Z")
    assert question.kind is DiscoveryFindingKind.UNRESOLVED_QUESTION
    assert question.related_finding_id == gap.id
    assert question.input_ids == gap.input_ids
    assert question.expectation == gap.expectation


def test_discovery_gap_round_trip_preserves_expectation():
    from episteme import detect_expected_gap

    first = make_record(
        RecordKind.OBSERVATION,
        {"name": "A"},
        (provenance(),),
        "2026-09-18T00:00:00Z",
    )
    second = make_record(
        RecordKind.OBSERVATION,
        {"name": "B"},
        (provenance(),),
        "2026-09-18T00:00:01Z",
    )

    with Store() as store:
        store.put_record(first)
        store.put_record(second)
        finding = detect_expected_gap(
            store,
            first.id,
            "related_to",
            second.id,
            "2026-09-18T00:00:02Z",
        )
        assert finding is not None
        store.put_discovery_finding(finding)
        restored = store.get_discovery_finding(finding.id)

    assert restored == finding
    assert restored is not None
    assert restored.expectation == DiscoveryExpectation(
        kind=DiscoveryExpectationKind.RELATIONSHIP,
        data={
            "subject_id": first.id,
            "predicate": "related_to",
            "object_id": second.id,
        },
    )


def test_unresolved_question_round_trip_preserves_expectation():
    from episteme import detect_expected_gap, question_from_finding

    first = make_record(
        RecordKind.OBSERVATION,
        {"name": "A"},
        (provenance(),),
        "2026-09-18T00:00:00Z",
    )
    second = make_record(
        RecordKind.OBSERVATION,
        {"name": "B"},
        (provenance(),),
        "2026-09-18T00:00:01Z",
    )

    with Store() as store:
        store.put_record(first)
        store.put_record(second)
        gap = detect_expected_gap(
            store,
            first.id,
            "related_to",
            second.id,
            "2026-09-18T00:00:02Z",
        )
        assert gap is not None
        question = question_from_finding(gap, "2026-09-18T00:00:03Z")
        store.put_discovery_finding(gap)
        store.put_discovery_finding(question)
        restored = store.get_discovery_finding(question.id)

    assert restored == question
    assert restored is not None
    assert restored.related_finding_id == gap.id
    assert restored.expectation == gap.expectation

def test_iter_discovery_findings_preserves_expectation():
    from episteme import detect_expected_gap

    first = make_record(
        RecordKind.OBSERVATION,
        {"name": "A"},
        (provenance(),),
        "2026-09-18T00:00:00Z",
    )
    second = make_record(
        RecordKind.OBSERVATION,
        {"name": "B"},
        (provenance(),),
        "2026-09-18T00:00:01Z",
    )

    with Store() as store:
        store.put_record(first)
        store.put_record(second)
        finding = detect_expected_gap(
            store,
            first.id,
            "related_to",
            second.id,
            "2026-09-18T00:00:02Z",
        )
        assert finding is not None
        store.put_discovery_finding(finding)
        restored = tuple(store.iter_discovery_findings())

    assert restored == (finding,)
    assert restored[0].expectation == DiscoveryExpectation(
        kind=DiscoveryExpectationKind.RELATIONSHIP,
        data={
            "subject_id": first.id,
            "predicate": "related_to",
            "object_id": second.id,
        },
    )



def test_question_generation_rejects_contradiction_findings():
    from episteme import (
        DiscoveryFinding,
        DiscoveryFindingKind,
        DiscoveryMeasure,
        question_from_finding,
    )

    finding = DiscoveryFinding(
        id="77777777-7777-4777-8777-777777777777",
        kind=DiscoveryFindingKind.CONTRADICTION,
        title="Explicit contradiction",
        description="Example contradiction",
        input_ids=(
            "11111111-1111-4111-8111-111111111111",
            "22222222-2222-4222-8222-222222222222",
        ),
        method="explicit-contradiction-discovery",
        method_version="1",
        rationale="Example",
        measures=(
            DiscoveryMeasure(
                name="input_count",
                value=2,
                scale="count",
                basis="two inputs",
            ),
        ),
        created_at="2026-09-18T00:00:03Z",
    )

    try:
        question_from_finding(finding, "2026-09-18T00:00:04Z")
    except ValueError as exc:
        assert str(exc) == "questions can only be generated from gap or tension findings"
    else:
        raise AssertionError("contradiction finding was accepted for question generation")



def test_store_rejects_discovery_finding_as_input():
    from episteme import DiscoveryExpectation, DiscoveryExpectationKind, DiscoveryFinding, DiscoveryFindingKind, DiscoveryMeasure

    first = make_record(
        RecordKind.OBSERVATION,
        {"name": "A"},
        (provenance(),),
        "2026-09-18T00:00:00Z",
    )
    second = make_record(
        RecordKind.OBSERVATION,
        {"name": "B"},
        (provenance(),),
        "2026-09-18T00:00:01Z",
    )
    generated = DiscoveryFinding(
        id="88888888-8888-4888-8888-888888888888",
        kind=DiscoveryFindingKind.CONTRADICTION,
        title="Generated finding",
        description="Example generated finding",
        input_ids=(first.id, second.id),
        method="example",
        method_version="1",
        rationale="Example",
        measures=(
            DiscoveryMeasure(
                name="input_count",
                value=2,
                scale="count",
                basis="two grounded inputs",
            ),
        ),
        created_at="2026-09-18T00:00:02Z",
    )
    downstream = DiscoveryFinding(
        id="99999999-9999-4999-8999-999999999999",
        kind=DiscoveryFindingKind.CONTRADICTION,
        title="Downstream finding",
        description="Must not use generated material as evidence",
        input_ids=(generated.id,),
        method="example",
        method_version="1",
        rationale="Example",
        measures=(
            DiscoveryMeasure(
                name="input_count",
                value=1,
                scale="count",
                basis="one generated input",
            ),
        ),
        created_at="2026-09-18T00:00:03Z",
    )

    with Store() as store:
        store.put_record(first)
        store.put_record(second)
        store.put_discovery_finding(generated)
        try:
            store.put_discovery_finding(downstream)
        except ValueError as exc:
            assert generated.id in str(exc)
        else:
            raise AssertionError("generated discovery finding was accepted as evidence")

def test_discovery_finding_rejects_unexpected_expectation():
    from episteme import DiscoveryFinding, DiscoveryFindingKind, DiscoveryMeasure

    first = "11111111-1111-4111-8111-111111111111"
    second = "22222222-2222-4222-8222-222222222222"

    try:
        DiscoveryFinding(
            id="33333333-3333-4333-8333-333333333333",
            kind=DiscoveryFindingKind.CONTRADICTION,
            title="Contradiction",
            description="Example",
            input_ids=(first, second),
            method="example",
            method_version="1",
            rationale="Example",
            measures=(
                DiscoveryMeasure(
                    name="input_count",
                    value=2,
                    scale="count",
                    basis="two inputs",
                ),
            ),
            created_at="2026-09-18T00:00:03Z",
            expectation=DiscoveryExpectation(DiscoveryExpectationKind.RELATIONSHIP, {"subject_id": first, "predicate": "contradicts", "object_id": second}),
        )
    except ValueError as exc:
        assert "only gap and unresolved-question findings" in str(exc)
    else:
        raise AssertionError("non-gap finding accepted an expectation")

def test_discovery_expectation_flows_from_gap_to_persisted_question():
    from episteme import (
        DiscoveryFindingKind,
        detect_expected_gap,
        question_from_finding,
    )

    first = make_record(
        RecordKind.OBSERVATION,
        {"name": "A"},
        (provenance(),),
        "2026-09-18T00:00:00Z",
    )
    second = make_record(
        RecordKind.OBSERVATION,
        {"name": "B"},
        (provenance(),),
        "2026-09-18T00:00:01Z",
    )

    with Store() as store:
        store.put_record(first)
        store.put_record(second)

        gap = detect_expected_gap(
            store,
            first.id,
            "related_to",
            second.id,
            "2026-09-18T00:00:02Z",
        )
        assert gap is not None
        assert gap.kind is DiscoveryFindingKind.GAP
        assert gap.input_ids == (first.id, second.id)
        assert gap.expectation == DiscoveryExpectation(DiscoveryExpectationKind.RELATIONSHIP, {"subject_id": first.id, "predicate": "related_to", "object_id": second.id})

        store.put_discovery_finding(gap)

        question = question_from_finding(
            gap,
            "2026-09-18T00:00:03Z",
        )
        assert question.kind is DiscoveryFindingKind.UNRESOLVED_QUESTION
        assert question.related_finding_id == gap.id
        assert question.input_ids == gap.input_ids
        assert question.expectation == gap.expectation

        store.put_discovery_finding(question)

        restored = store.get_discovery_finding(question.id)
        iterated = tuple(store.iter_discovery_findings())

    assert restored == question
    assert restored is not None
    assert restored.related_finding_id == gap.id
    assert restored.input_ids == (first.id, second.id)
    assert restored.expectation == DiscoveryExpectation(DiscoveryExpectationKind.RELATIONSHIP, {"subject_id": first.id, "predicate": "related_to", "object_id": second.id})
    assert all(item.id != question.id for item in iterated if item.kind is DiscoveryFindingKind.GAP)



def _phase4_finding(first, second):
    from episteme import DiscoveryFinding, DiscoveryFindingKind, DiscoveryMeasure
    return DiscoveryFinding(
        id="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        kind=DiscoveryFindingKind.GAP,
        title="Expected relation is absent",
        description="An explicitly expected relationship is not represented.",
        input_ids=(first.id, second.id),
        method="expectation-gap-detection",
        method_version="1",
        rationale="The explicit expectation is not present.",
        measures=(DiscoveryMeasure("input_count", 2, "count", "two inputs"),),
        created_at="2026-09-18T00:00:02Z",
        expectation=DiscoveryExpectation(DiscoveryExpectationKind.RELATIONSHIP, {"subject_id": first.id, "predicate": "related_to", "object_id": second.id}),
    )


def test_hypothesis_round_trip_preserves_findings_and_assumptions():
    from episteme import Hypothesis

    first = make_record(RecordKind.OBSERVATION, {"name": "A"}, (provenance(),), "2026-09-18T00:00:00Z")
    second = make_record(RecordKind.OBSERVATION, {"name": "B"}, (provenance(),), "2026-09-18T00:00:01Z")
    finding = _phase4_finding(first, second)
    hypothesis = Hypothesis(
        id="bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
        statement="A hidden relation may explain the observed pattern.",
        finding_ids=(finding.id,),
        input_ids=(first.id, second.id),
        method="manual-hypothesis",
        method_version="1",
        rationale="The missing relation motivates this candidate explanation.",
        assumptions=("The observations are comparable.",),
        created_at="2026-09-18T00:00:03Z",
    )

    with Store() as store:
        store.put_record(first)
        store.put_record(second)
        store.put_discovery_finding(finding)
        store.put_hypothesis(hypothesis)
        assert store.get_hypothesis(hypothesis.id) == hypothesis
        assert tuple(store.iter_hypotheses()) == (hypothesis,)


def test_store_rejects_hypothesis_without_existing_finding():
    from episteme import Hypothesis

    hypothesis = Hypothesis(
        id="cccccccc-cccc-4ccc-8ccc-cccccccccccc",
        statement="Candidate explanation",
        finding_ids=("dddddddd-dddd-4ddd-8ddd-dddddddddddd",),
        input_ids=(),
        method="manual",
        method_version="1",
        rationale="Example",
        assumptions=(),
        created_at="2026-09-18T00:00:00Z",
    )

    with Store() as store:
        try:
            store.put_hypothesis(hypothesis)
        except ValueError as exc:
            assert hypothesis.finding_ids[0] in str(exc)
        else:
            raise AssertionError("hypothesis with missing finding was accepted")


def test_competing_hypotheses_remain_distinct_and_can_share_finding():
    from episteme import Hypothesis

    first_record = make_record(RecordKind.OBSERVATION, {"name": "A"}, (provenance(),), "2026-09-18T00:00:00Z")
    second_record = make_record(RecordKind.OBSERVATION, {"name": "B"}, (provenance(),), "2026-09-18T00:00:01Z")
    finding = _phase4_finding(first_record, second_record)
    common = dict(
        finding_ids=(finding.id,), input_ids=(), method="manual", method_version="1",
        rationale="Two alternatives are retained.", assumptions=(),
        created_at="2026-09-18T00:00:03Z",
    )
    first = Hypothesis(id="eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee", statement="Explanation A", **common)
    second = Hypothesis(id="ffffffff-ffff-4fff-8fff-ffffffffffff", statement="Explanation B", **common)

    with Store() as store:
        store.put_record(first_record)
        store.put_record(second_record)
        store.put_discovery_finding(finding)
        store.put_hypothesis(first)
        store.put_hypothesis(second)
        assert tuple(store.iter_hypotheses()) == (first, second)


def test_prediction_round_trip_preserves_distinguishing_consequence():
    from episteme import Hypothesis, Prediction

    first_record = make_record(RecordKind.OBSERVATION, {"name": "A"}, (provenance(),), "2026-09-18T00:00:00Z")
    second_record = make_record(RecordKind.OBSERVATION, {"name": "B"}, (provenance(),), "2026-09-18T00:00:01Z")
    finding = _phase4_finding(first_record, second_record)
    first = Hypothesis(
        id="12121212-1212-4121-8121-121212121212", statement="Explanation A",
        finding_ids=(finding.id,), input_ids=(), method="manual", method_version="1",
        rationale="Example", assumptions=("Condition A holds.",), created_at="2026-09-18T00:00:03Z",
    )
    second = Hypothesis(
        id="13131313-1313-4131-8131-131313131313", statement="Explanation B",
        finding_ids=(finding.id,), input_ids=(), method="manual", method_version="1",
        rationale="Example", assumptions=("Condition B holds.",), created_at="2026-09-18T00:00:04Z",
    )
    prediction = Prediction(
        id="14141414-1414-4141-8141-141414141414", source_id=first.id,
        consequence="The measured response will increase.",
        conditions="Under the stated test conditions.",
        assumptions=("The system is stable.",),
        method="manual-prediction", method_version="1",
        rationale="This consequence differs from the competing explanation.",
        comparison_hypothesis_ids=(first.id, second.id),
        created_at="2026-09-18T00:00:05Z",
    )

    with Store() as store:
        store.put_record(first_record)
        store.put_record(second_record)
        store.put_discovery_finding(finding)
        store.put_hypothesis(first)
        store.put_hypothesis(second)
        store.put_prediction(prediction)
        assert store.get_prediction(prediction.id) == prediction
        assert tuple(store.iter_predictions()) == (prediction,)


def test_prediction_rejects_unknown_comparison_hypothesis():
    from episteme import Hypothesis, Prediction

    first_record = make_record(
        RecordKind.OBSERVATION,
        {"name": "A"},
        (provenance(),),
        "2026-09-18T00:00:00Z",
    )
    second_record = make_record(
        RecordKind.OBSERVATION,
        {"name": "B"},
        (provenance(),),
        "2026-09-18T00:00:01Z",
    )
    finding = _phase4_finding(first_record, second_record)
    first = Hypothesis(
        id="15151515-1515-4151-8151-151515151515", statement="Explanation",
        finding_ids=(finding.id,), input_ids=(),
        method="manual", method_version="1", rationale="Example", assumptions=(),
        created_at="2026-09-18T00:00:03Z",
    )
    prediction = Prediction(
        id="17171717-1717-4171-8171-171717171717", source_id=first.id,
        consequence="A consequence.", conditions="A bounded condition.",
        assumptions=(), method="manual", method_version="1", rationale="Example",
        comparison_hypothesis_ids=(first.id, "18181818-1818-4181-8181-181818181818"),
        created_at="2026-09-18T00:00:04Z",
    )

    with Store() as store:
        store.put_record(first_record)
        store.put_record(second_record)
        store.put_discovery_finding(finding)
        store.put_hypothesis(first)
        try:
            store.put_prediction(prediction)
        except ValueError as exc:
            assert "18181818-1818-4181-8181-181818181818" in str(exc)
        else:
            raise AssertionError("prediction with missing comparison hypothesis was accepted")


def test_propose_hypothesis_preserves_explicit_content():
    from episteme import propose_hypothesis

    hypothesis = propose_hypothesis(
        statement="A proposed explanation.",
        finding_ids=("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",),
        input_ids=("11111111-1111-4111-8111-111111111111",),
        method="deterministic-test",
        method_version="1",
        rationale="Explicitly supplied rationale.",
        assumptions=("Assumption one.",),
        created_at="2026-09-18T00:00:10Z",
    )

    assert hypothesis.statement == "A proposed explanation."
    assert hypothesis.finding_ids == ("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",)
    assert hypothesis.input_ids == ("11111111-1111-4111-8111-111111111111",)
    assert hypothesis.assumptions == ("Assumption one.",)


def test_represent_model_preserves_explicit_hypotheses_and_assumptions():
    from episteme import represent_model

    model = represent_model(
        description="A structured explanatory mechanism.",
        hypothesis_ids=("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",),
        assumptions=("The system is stable.",),
        method="deterministic-test",
        method_version="1",
        rationale="Explicitly supplied model description.",
        created_at="2026-09-18T00:00:11Z",
    )

    assert model.hypothesis_ids == ("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",)
    assert model.assumptions == ("The system is stable.",)


def test_predict_preserves_explicit_consequence_and_comparison():
    from episteme import predict

    prediction = predict(
        source_id="bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
        consequence="The measured response will differ.",
        conditions="Under the stated conditions.",
        assumptions=("The instrument remains calibrated.",),
        method="deterministic-test",
        method_version="1",
        rationale="Explicitly supplied distinguishing consequence.",
        comparison_hypothesis_ids=(
            "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
            "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
        ),
        created_at="2026-09-18T00:00:12Z",
    )

    assert prediction.consequence == "The measured response will differ."
    assert prediction.comparison_hypothesis_ids == (
        "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
        "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
    )
    assert prediction.assumptions == ("The instrument remains calibrated.",)


def test_phase4_end_to_end_preserves_grounded_to_prediction_lineage():
    from episteme import (
        detect_expected_gap,
        predict,
        propose_hypothesis,
    )

    first = make_record(
        RecordKind.OBSERVATION,
        {"name": "A"},
        (provenance(),),
        "2026-09-18T00:00:00Z",
    )
    second = make_record(
        RecordKind.OBSERVATION,
        {"name": "B"},
        (provenance(),),
        "2026-09-18T00:00:01Z",
    )

    with Store() as store:
        store.put_record(first)
        store.put_record(second)

        finding = detect_expected_gap(
            store,
            first.id,
            "related_to",
            second.id,
            "2026-09-18T00:00:02Z",
        )
        assert finding is not None
        store.put_discovery_finding(finding)

        hypothesis = propose_hypothesis(
            statement="A hidden relation may explain the observed pattern.",
            finding_ids=(finding.id,),
            input_ids=(first.id, second.id),
            method="deterministic-test",
            method_version="1",
            rationale="The explicit gap motivates this candidate explanation.",
            assumptions=("The observations are comparable.",),
            created_at="2026-09-18T00:00:03Z",
        )
        store.put_hypothesis(hypothesis)

        prediction = predict(
            source_id=hypothesis.id,
            consequence="The measured relationship will be observed under test.",
            conditions="When the stated observation conditions are reproduced.",
            assumptions=("The observations remain comparable.",),
            method="deterministic-test",
            method_version="1",
            rationale="This is a bounded consequence of the candidate hypothesis.",
            created_at="2026-09-18T00:00:04Z",
        )
        store.put_prediction(prediction)

        restored_finding = store.get_discovery_finding(finding.id)
        restored_hypothesis = store.get_hypothesis(hypothesis.id)
        restored_prediction = store.get_prediction(prediction.id)

    assert restored_finding is not None
    assert restored_hypothesis is not None
    assert restored_prediction is not None
    assert restored_hypothesis.finding_ids == (restored_finding.id,)
    assert restored_hypothesis.input_ids == (first.id, second.id)
    assert restored_prediction.source_id == restored_hypothesis.id
    assert restored_prediction.source_id != first.id
    assert restored_prediction.source_id != second.id


def test_competing_hypotheses_produce_explicit_distinguishing_predictions():
    from episteme import predict, propose_hypothesis

    first_record = make_record(
        RecordKind.OBSERVATION,
        {"name": "A"},
        (provenance(),),
        "2026-09-18T00:00:00Z",
    )
    second_record = make_record(
        RecordKind.OBSERVATION,
        {"name": "B"},
        (provenance(),),
        "2026-09-18T00:00:01Z",
    )

    with Store() as store:
        store.put_record(first_record)
        store.put_record(second_record)

        finding = _phase4_finding(first_record, second_record)
        store.put_discovery_finding(finding)

        first = propose_hypothesis(
            statement="Explanation A accounts for the missing relation.",
            finding_ids=(finding.id,),
            method="deterministic-test",
            method_version="1",
            rationale="Candidate explanation A.",
            created_at="2026-09-18T00:00:03Z",
        )
        second = propose_hypothesis(
            statement="Explanation B accounts for the missing relation.",
            finding_ids=(finding.id,),
            method="deterministic-test",
            method_version="1",
            rationale="Candidate explanation B.",
            created_at="2026-09-18T00:00:04Z",
        )
        store.put_hypothesis(first)
        store.put_hypothesis(second)

        first_prediction = predict(
            source_id=first.id,
            consequence="Outcome A will occur.",
            conditions="Under condition X.",
            method="deterministic-test",
            method_version="1",
            rationale="This consequence is specific to Explanation A.",
            comparison_hypothesis_ids=(first.id, second.id),
            created_at="2026-09-18T00:00:05Z",
        )
        second_prediction = predict(
            source_id=second.id,
            consequence="Outcome B will occur.",
            conditions="Under condition X.",
            method="deterministic-test",
            method_version="1",
            rationale="This consequence is specific to Explanation B.",
            comparison_hypothesis_ids=(first.id, second.id),
            created_at="2026-09-18T00:00:06Z",
        )
        store.put_prediction(first_prediction)
        store.put_prediction(second_prediction)

        restored = tuple(store.iter_predictions())

    assert len(restored) == 2
    assert restored[0].source_id == first.id
    assert restored[1].source_id == second.id
    assert restored[0].comparison_hypothesis_ids == (first.id, second.id)
    assert restored[1].comparison_hypothesis_ids == (first.id, second.id)
    assert restored[0].consequence != restored[1].consequence
    assert restored[0].conditions == restored[1].conditions


def test_experiment_proposal_round_trip_preserves_prediction_lineage():
    from episteme import propose_experiment, predict, propose_hypothesis

    first = make_record(RecordKind.OBSERVATION, {"name": "A"}, (provenance(),), "2026-09-18T00:00:00Z")
    second = make_record(RecordKind.OBSERVATION, {"name": "B"}, (provenance(),), "2026-09-18T00:00:01Z")

    with Store() as store:
        store.put_record(first)
        store.put_record(second)
        finding = _phase4_finding(first, second)
        store.put_discovery_finding(finding)

        hypothesis_a = propose_hypothesis(
            statement="Explanation A.",
            finding_ids=(finding.id,),
            method="test",
            method_version="1",
            rationale="Candidate A.",
            created_at="2026-09-18T00:00:02Z",
        )
        hypothesis_b = propose_hypothesis(
            statement="Explanation B.",
            finding_ids=(finding.id,),
            method="test",
            method_version="1",
            rationale="Candidate B.",
            created_at="2026-09-18T00:00:03Z",
        )
        store.put_hypothesis(hypothesis_a)
        store.put_hypothesis(hypothesis_b)

        prediction_a = predict(
            source_id=hypothesis_a.id,
            consequence="Outcome A.",
            conditions="Same test condition.",
            method="test",
            method_version="1",
            rationale="Distinguishing consequence A.",
            comparison_hypothesis_ids=(hypothesis_a.id, hypothesis_b.id),
            created_at="2026-09-18T00:00:04Z",
        )
        prediction_b = predict(
            source_id=hypothesis_b.id,
            consequence="Outcome B.",
            conditions="Same test condition.",
            method="test",
            method_version="1",
            rationale="Distinguishing consequence B.",
            comparison_hypothesis_ids=(hypothesis_a.id, hypothesis_b.id),
            created_at="2026-09-18T00:00:05Z",
        )
        store.put_prediction(prediction_a)
        store.put_prediction(prediction_b)

        proposal = propose_experiment(
            prediction_ids=(prediction_a.id, prediction_b.id),
            objective="Distinguish the competing explanations.",
            proposed_observation="Measure the outcome under the shared test condition.",
            discrimination_basis="The competing predictions specify different outcomes under the same condition.",
            conditions="Same test condition.",
            assumptions=("The measurement remains comparable.",),
            method="test",
            method_version="1",
            rationale="The proposed observation targets the explicit difference between predictions.",
            created_at="2026-09-18T00:00:06Z",
        )
        store.put_experiment_proposal(proposal)

        restored = store.get_experiment_proposal(proposal.id)

    assert restored == proposal
    assert restored is not None
    assert restored.prediction_ids == (prediction_a.id, prediction_b.id)
    assert restored.proposed_observation == "Measure the outcome under the shared test condition."


def test_store_rejects_experiment_proposal_without_existing_prediction():
    from episteme import ExperimentProposal

    proposal = ExperimentProposal(
        id="19191919-1919-4191-8191-191919191919",
        prediction_ids=("20202020-2020-4202-8202-202020202020",),
        objective="Test a prediction.",
        proposed_observation="Observe the stated consequence.",
        discrimination_basis="The observation could distinguish the stated prediction.",
        conditions="Under stated conditions.",
        assumptions=(),
        method="manual",
        method_version="1",
        rationale="Example.",
        created_at="2026-09-18T00:00:00Z",
    )

    with Store() as store:
        try:
            store.put_experiment_proposal(proposal)
        except ValueError as exc:
            assert proposal.prediction_ids[0] in str(exc)
        else:
            raise AssertionError("proposal with missing prediction was accepted")


def test_propose_experiment_preserves_explicit_content():
    from episteme import propose_experiment

    proposal = propose_experiment(
        prediction_ids=(
            "21212121-2121-4121-8121-212121212121",
            "22222222-2222-4222-8222-222222222222",
        ),
        objective="Determine which predicted consequence occurs.",
        proposed_observation="Measure the response.",
        discrimination_basis="The competing predictions imply different measurable responses.",
        conditions="Under the bounded test conditions.",
        assumptions=("The instrument is calibrated.",),
        method="deterministic-test",
        method_version="1",
        rationale="Explicitly supplied experiment plan.",
        created_at="2026-09-18T00:00:00Z",
    )

    assert proposal.prediction_ids == (
        "21212121-2121-4121-8121-212121212121",
        "22222222-2222-4222-8222-222222222222",
    )
    assert proposal.objective == "Determine which predicted consequence occurs."
    assert proposal.proposed_observation == "Measure the response."
    assert proposal.assumptions == ("The instrument is calibrated.",)


def test_result_can_be_related_to_proposal_and_predictions_without_promoting_them():
    from episteme import Relationship, propose_experiment, predict, propose_hypothesis

    first_record = make_record(
        RecordKind.OBSERVATION,
        {"name": "A"},
        (provenance(),),
        "2026-09-18T00:00:00Z",
    )
    second_record = make_record(
        RecordKind.OBSERVATION,
        {"name": "B"},
        (provenance(),),
        "2026-09-18T00:00:01Z",
    )
    result = make_record(
        RecordKind.RESULT,
        {"observed": "Outcome A"},
        (provenance(),),
        "2026-09-18T00:00:07Z",
    )

    with Store() as store:
        store.put_record(first_record)
        store.put_record(second_record)
        store.put_record(result)

        finding = _phase4_finding(first_record, second_record)
        store.put_discovery_finding(finding)

        hypothesis_a = propose_hypothesis(
            statement="Explanation A.",
            finding_ids=(finding.id,),
            method="test",
            method_version="1",
            rationale="Candidate A.",
            created_at="2026-09-18T00:00:02Z",
        )
        hypothesis_b = propose_hypothesis(
            statement="Explanation B.",
            finding_ids=(finding.id,),
            method="test",
            method_version="1",
            rationale="Candidate B.",
            created_at="2026-09-18T00:00:03Z",
        )
        store.put_hypothesis(hypothesis_a)
        store.put_hypothesis(hypothesis_b)

        prediction_a = predict(
            source_id=hypothesis_a.id,
            consequence="Outcome A.",
            conditions="Same test condition.",
            method="test",
            method_version="1",
            rationale="Prediction A.",
            comparison_hypothesis_ids=(hypothesis_a.id, hypothesis_b.id),
            created_at="2026-09-18T00:00:04Z",
        )
        prediction_b = predict(
            source_id=hypothesis_b.id,
            consequence="Outcome B.",
            conditions="Same test condition.",
            method="test",
            method_version="1",
            rationale="Prediction B.",
            comparison_hypothesis_ids=(hypothesis_a.id, hypothesis_b.id),
            created_at="2026-09-18T00:00:05Z",
        )
        store.put_prediction(prediction_a)
        store.put_prediction(prediction_b)

        proposal = propose_experiment(
            prediction_ids=(prediction_a.id, prediction_b.id),
            objective="Distinguish the competing explanations.",
            proposed_observation="Measure the outcome under the shared test condition.",
            discrimination_basis="The predictions specify different outcomes under the same condition.",
            conditions="Same test condition.",
            assumptions=("The measurement remains comparable.",),
            method="test",
            method_version="1",
            rationale="The proposal targets the distinguishing consequences.",
            created_at="2026-09-18T00:00:06Z",
        )
        store.put_experiment_proposal(proposal)

        result_link = Relationship(
            id="23232323-2323-4232-8232-232323232323",
            subject_id=result.id,
            predicate="resulted_from",
            object_id=proposal.id,
            provenance=(provenance(),),
            created_at="2026-09-18T00:00:08Z",
        )
        prediction_link = Relationship(
            id="24242424-2424-4242-8242-242424242424",
            subject_id=result.id,
            predicate="tests",
            object_id=prediction_a.id,
            provenance=(provenance(),),
            created_at="2026-09-18T00:00:09Z",
        )
        store.put_relationship(result_link)
        store.put_relationship(prediction_link)

        restored = tuple(store.iter_relationships())

    assert restored == (result_link, prediction_link)
    assert restored[0].subject_id == result.id
    assert restored[0].object_id == proposal.id
    assert restored[1].object_id == prediction_a.id


def test_prediction_evaluation_round_trip_preserves_result_prediction_and_proposal():
    from episteme import (
        PredictionEvaluation,
        PredictionEvaluationOutcome,
        propose_experiment,
        predict,
        propose_hypothesis,
    )

    first = make_record(
        RecordKind.OBSERVATION,
        {"name": "A"},
        (provenance(),),
        "2026-09-18T00:00:00Z",
    )
    second = make_record(
        RecordKind.OBSERVATION,
        {"name": "B"},
        (provenance(),),
        "2026-09-18T00:00:01Z",
    )
    result = make_record(
        RecordKind.RESULT,
        {"observed": "Outcome A"},
        (provenance(),),
        "2026-09-18T00:00:07Z",
    )

    with Store() as store:
        store.put_record(first)
        store.put_record(second)
        store.put_record(result)

        finding = _phase4_finding(first, second)
        store.put_discovery_finding(finding)

        hypothesis_a = propose_hypothesis(
            statement="Explanation A.",
            finding_ids=(finding.id,),
            method="test",
            method_version="1",
            rationale="Candidate A.",
            created_at="2026-09-18T00:00:02Z",
        )
        hypothesis_b = propose_hypothesis(
            statement="Explanation B.",
            finding_ids=(finding.id,),
            method="test",
            method_version="1",
            rationale="Candidate B.",
            created_at="2026-09-18T00:00:03Z",
        )
        store.put_hypothesis(hypothesis_a)
        store.put_hypothesis(hypothesis_b)

        prediction = predict(
            source_id=hypothesis_a.id,
            consequence="Outcome A.",
            conditions="Same test condition.",
            method="test",
            method_version="1",
            rationale="Prediction A.",
            comparison_hypothesis_ids=(hypothesis_a.id, hypothesis_b.id),
            created_at="2026-09-18T00:00:04Z",
        )
        store.put_prediction(prediction)

        proposal = propose_experiment(
            prediction_ids=(prediction.id,),
            objective="Test the predicted consequence.",
            proposed_observation="Measure the outcome.",
            discrimination_basis="The observed outcome can be compared directly with the prediction.",
            conditions="Same test condition.",
            assumptions=("The measurement is comparable.",),
            method="test",
            method_version="1",
            rationale="The proposal obtains the observation needed for comparison.",
            created_at="2026-09-18T00:00:06Z",
        )
        store.put_experiment_proposal(proposal)

        before = store.get_prediction(prediction.id)
        evaluations = []
        for number, outcome in enumerate(PredictionEvaluationOutcome, start=1):
            evaluation = PredictionEvaluation(
                id=f"30{number:02d}0303-0303-4303-8303-030303030303",
                result_id=result.id,
                prediction_id=prediction.id,
                experiment_proposal_id=proposal.id,
                comparison_conditions="Same test condition.",
                assumptions=("The measurement is comparable.",),
                outcome=outcome,
                rationale=f"Evaluation classified as {outcome.value}.",
                method="comparison",
                method_version="1",
                created_at=f"2026-09-18T00:00:{10 + number:02d}Z",
            )
            store.put_prediction_evaluation(evaluation)
            evaluations.append(evaluation)

        restored = tuple(store.iter_prediction_evaluations())
        after = store.get_prediction(prediction.id)

    assert restored == tuple(evaluations)
    assert [item.outcome for item in restored] == list(PredictionEvaluationOutcome)
    assert before == after
    assert all(item.result_id == result.id for item in restored)
    assert all(item.prediction_id == prediction.id for item in restored)
    assert all(item.experiment_proposal_id == proposal.id for item in restored)


def test_prediction_evaluation_requires_grounded_result_existing_prediction_and_matching_proposal():
    from episteme import (
        PredictionEvaluation,
        PredictionEvaluationOutcome,
        propose_hypothesis,
        predict,
        propose_experiment,
    )

    first = make_record(
        RecordKind.OBSERVATION,
        {"name": "A"},
        (provenance(),),
        "2026-09-18T00:00:00Z",
    )
    second = make_record(
        RecordKind.OBSERVATION,
        {"name": "B"},
        (provenance(),),
        "2026-09-18T00:00:01Z",
    )
    not_a_result = make_record(
        RecordKind.OBSERVATION,
        {"observed": "Not a result"},
        (provenance(),),
        "2026-09-18T00:00:07Z",
    )
    result = make_record(
        RecordKind.RESULT,
        {"observed": "Outcome"},
        (provenance(),),
        "2026-09-18T00:00:08Z",
    )

    with Store() as store:
        store.put_record(first)
        store.put_record(second)
        store.put_record(not_a_result)
        store.put_record(result)

        finding = _phase4_finding(first, second)
        store.put_discovery_finding(finding)
        hypothesis = propose_hypothesis(
            statement="Explanation.",
            finding_ids=(finding.id,),
            method="test",
            method_version="1",
            rationale="Candidate explanation.",
            created_at="2026-09-18T00:00:02Z",
        )
        store.put_hypothesis(hypothesis)
        prediction = predict(
            source_id=hypothesis.id,
            consequence="Outcome.",
            conditions="Same test condition.",
            method="test",
            method_version="1",
            rationale="Bounded prediction.",
            created_at="2026-09-18T00:00:03Z",
        )
        other_prediction = predict(
            source_id=hypothesis.id,
            consequence="Other outcome.",
            conditions="Different test condition.",
            method="test",
            method_version="1",
            rationale="Second bounded prediction.",
            created_at="2026-09-18T00:00:03Z",
        )
        store.put_prediction(prediction)
        store.put_prediction(other_prediction)

        proposal = propose_experiment(
            prediction_ids=(prediction.id,),
            objective="Test prediction.",
            proposed_observation="Measure outcome.",
            discrimination_basis="The measurement tests the predicted consequence.",
            conditions="Same test condition.",
            assumptions=(),
            method="test",
            method_version="1",
            rationale="Direct test.",
            created_at="2026-09-18T00:00:04Z",
        )
        other_proposal = propose_experiment(
            prediction_ids=(other_prediction.id,),
            objective="Test another prediction.",
            proposed_observation="Measure another outcome.",
            discrimination_basis="The measurement tests the other predicted consequence.",
            conditions="Different test condition.",
            assumptions=(),
            method="test",
            method_version="1",
            rationale="Direct test.",
            created_at="2026-09-18T00:00:04Z",
        )
        store.put_experiment_proposal(proposal)
        store.put_experiment_proposal(other_proposal)

        bad_result = PredictionEvaluation(
            id="31313131-3131-4131-8131-313131313131",
            result_id=not_a_result.id,
            prediction_id=prediction.id,
            experiment_proposal_id=proposal.id,
            comparison_conditions="Same test condition.",
            assumptions=(),
            outcome=PredictionEvaluationOutcome.INCONCLUSIVE,
            rationale="Cannot compare.",
            method="comparison",
            method_version="1",
            created_at="2026-09-18T00:00:05Z",
        )
        try:
            store.put_prediction_evaluation(bad_result)
        except ValueError as exc:
            assert not_a_result.id in str(exc)
        else:
            raise AssertionError("non-result record was accepted for evaluation")

        missing_prediction = PredictionEvaluation(
            id="32323232-3232-4232-8232-323232323232",
            result_id=result.id,
            prediction_id="33333333-3333-4333-8333-333333333333",
            experiment_proposal_id=None,
            comparison_conditions="Same test condition.",
            assumptions=(),
            outcome=PredictionEvaluationOutcome.INCONCLUSIVE,
            rationale="Cannot compare.",
            method="comparison",
            method_version="1",
            created_at="2026-09-18T00:00:06Z",
        )
        try:
            store.put_prediction_evaluation(missing_prediction)
        except ValueError as exc:
            assert missing_prediction.prediction_id in str(exc)
        else:
            raise AssertionError("missing prediction was accepted for evaluation")

        mismatched_proposal = PredictionEvaluation(
            id="34343434-3434-4434-8434-343434343434",
            result_id=result.id,
            prediction_id=prediction.id,
            experiment_proposal_id=other_proposal.id,
            comparison_conditions="Same test condition.",
            assumptions=(),
            outcome=PredictionEvaluationOutcome.INCONCLUSIVE,
            rationale="Proposal does not contain this prediction.",
            method="comparison",
            method_version="1",
            created_at="2026-09-18T00:00:07Z",
        )
        try:
            store.put_prediction_evaluation(mismatched_proposal)
        except ValueError as exc:
            assert prediction.id in str(exc)
        else:
            raise AssertionError("evaluation accepted a proposal that did not test its prediction")


def test_knowledge_state_consequence_round_trip_preserves_contextual_transition():
    from episteme import (
        KnowledgeStateConsequence,
        KnowledgeStateConsequenceKind,
        KnowledgeStateTargetKind,
    )

    consequence = KnowledgeStateConsequence(
        id="35353535-3535-4535-8535-353535353535",
        evaluation_ids=("36363636-3636-4636-8636-363636363636",),
        target_kind=KnowledgeStateTargetKind.HYPOTHESIS,
        target_id="37373737-3737-4737-8737-373737373737",
        consequence=KnowledgeStateConsequenceKind.WEAKENS,
        assumptions=("The comparison conditions remain valid.",),
        rationale="The evaluated result conflicts with an expected consequence under the stated assumptions.",
        method="manual-comparison",
        method_version="1",
        created_at="2026-09-18T00:00:00Z",
    )

    assert KnowledgeStateConsequence.from_dict(consequence.to_dict()) == consequence


def test_store_rejects_discovery_finding_with_unknown_generated_context():
    from episteme import DiscoveryFinding, DiscoveryFindingKind

    record = make_record(
        RecordKind.OBSERVATION,
        {"name": "context test"},
        (provenance(),),
        "2026-09-18T00:00:00Z",
    )
    finding = DiscoveryFinding(
        id="38383838-3838-4838-8838-383838383838",
        kind=DiscoveryFindingKind.TENSION,
        title="Generated context test",
        description="A finding with an intentionally unknown generated context identifier.",
        input_ids=(record.id,),
        context_ids=("39393939-3939-4939-8939-393939393939",),
        method="test",
        method_version="1",
        rationale="Unknown generated context must not be silently accepted.",
        measures=(),
        created_at="2026-09-18T00:00:01Z",
    )

    with Store() as store:
        store.put_record(record)
        try:
            store.put_discovery_finding(finding)
        except ValueError as exc:
            assert finding.context_ids[0] in str(exc)
        else:
            raise AssertionError("unknown generated context was accepted")


def test_renewed_discovery_surfaces_differing_evaluations_without_promoting_context():
    from episteme import (
        DiscoveryFindingKind,
        PredictionEvaluation,
        PredictionEvaluationOutcome,
        propose_hypothesis,
        predict,
        discover_evaluation_tensions,
    )

    first = make_record(
        RecordKind.OBSERVATION,
        {"name": "A"},
        (provenance(),),
        "2026-09-18T00:00:00Z",
    )
    second = make_record(
        RecordKind.OBSERVATION,
        {"name": "B"},
        (provenance(),),
        "2026-09-18T00:00:01Z",
    )
    result_a = make_record(
        RecordKind.RESULT,
        {"observed": "Outcome A"},
        (provenance(),),
        "2026-09-18T00:00:07Z",
    )
    result_b = make_record(
        RecordKind.RESULT,
        {"observed": "Outcome B"},
        (provenance(),),
        "2026-09-18T00:00:08Z",
    )

    with Store() as store:
        for record in (first, second, result_a, result_b):
            store.put_record(record)

        finding = _phase4_finding(first, second)
        store.put_discovery_finding(finding)
        hypothesis = propose_hypothesis(
            statement="Explanation.",
            finding_ids=(finding.id,),
            method="test",
            method_version="1",
            rationale="Candidate explanation.",
            created_at="2026-09-18T00:00:02Z",
        )
        store.put_hypothesis(hypothesis)
        prediction = predict(
            source_id=hypothesis.id,
            consequence="Outcome A.",
            conditions="Same test condition.",
            assumptions=("The measurement is comparable.",),
            method="test",
            method_version="1",
            rationale="Bounded prediction.",
            created_at="2026-09-18T00:00:03Z",
        )
        store.put_prediction(prediction)

        evaluation_a = PredictionEvaluation(
            id="41414141-4141-4141-8141-414141414141",
            result_id=result_a.id,
            prediction_id=prediction.id,
            experiment_proposal_id=None,
            comparison_conditions="Same test condition.",
            assumptions=("The measurement is comparable.",),
            outcome=PredictionEvaluationOutcome.CONSISTENT,
            rationale="Result A is compatible with the prediction.",
            method="comparison",
            method_version="1",
            created_at="2026-09-18T00:00:09Z",
        )
        evaluation_b = PredictionEvaluation(
            id="42424242-4242-4242-8242-424242424242",
            result_id=result_b.id,
            prediction_id=prediction.id,
            experiment_proposal_id=None,
            comparison_conditions="Same test condition.",
            assumptions=("The measurement is comparable.",),
            outcome=PredictionEvaluationOutcome.INCONSISTENT,
            rationale="Result B conflicts with the prediction.",
            method="comparison",
            method_version="1",
            created_at="2026-09-18T00:00:10Z",
        )
        store.put_prediction_evaluation(evaluation_a)
        store.put_prediction_evaluation(evaluation_b)

        findings = discover_evaluation_tensions(
            store,
            created_at="2026-09-18T00:00:11Z",
        )

        assert len(findings) == 1
        renewed = findings[0]
        assert renewed.kind is DiscoveryFindingKind.TENSION
        assert renewed.input_ids == (result_a.id, result_b.id)
        assert renewed.context_ids == (evaluation_a.id, evaluation_b.id)
        assert evaluation_a.id not in renewed.input_ids
        assert evaluation_b.id not in renewed.input_ids

        store.put_discovery_finding(renewed)
        restored = store.get_discovery_finding(renewed.id)

    assert restored == renewed


def test_renewed_discovery_does_not_merge_different_comparison_contexts():
    from episteme import (
        PredictionEvaluation,
        PredictionEvaluationOutcome,
        propose_hypothesis,
        predict,
        discover_evaluation_tensions,
    )

    first = make_record(RecordKind.OBSERVATION, {"name": "A"}, (provenance(),), "2026-09-18T00:00:00Z")
    second = make_record(RecordKind.OBSERVATION, {"name": "B"}, (provenance(),), "2026-09-18T00:00:01Z")
    result_a = make_record(RecordKind.RESULT, {"observed": "A"}, (provenance(),), "2026-09-18T00:00:07Z")
    result_b = make_record(RecordKind.RESULT, {"observed": "B"}, (provenance(),), "2026-09-18T00:00:08Z")

    with Store() as store:
        for record in (first, second, result_a, result_b):
            store.put_record(record)
        finding = _phase4_finding(first, second)
        store.put_discovery_finding(finding)
        hypothesis = propose_hypothesis(
            statement="Explanation.",
            finding_ids=(finding.id,),
            method="test",
            method_version="1",
            rationale="Candidate explanation.",
            created_at="2026-09-18T00:00:02Z",
        )
        store.put_hypothesis(hypothesis)
        prediction = predict(
            source_id=hypothesis.id,
            consequence="Outcome.",
            conditions="Bounded conditions.",
            method="test",
            method_version="1",
            rationale="Bounded prediction.",
            created_at="2026-09-18T00:00:03Z",
        )
        store.put_prediction(prediction)

        for evaluation_id, result_id, condition, outcome, second_offset in (
            ("43434343-4343-4343-8343-434343434343", result_a.id, "Condition A", PredictionEvaluationOutcome.CONSISTENT, 0),
            ("44444444-4444-4444-8444-444444444444", result_b.id, "Condition B", PredictionEvaluationOutcome.INCONSISTENT, 1),
        ):
            store.put_prediction_evaluation(
                PredictionEvaluation(
                    id=evaluation_id,
                    result_id=result_id,
                    prediction_id=prediction.id,
                    experiment_proposal_id=None,
                    comparison_conditions=condition,
                    assumptions=(),
                    outcome=outcome,
                    rationale="Context-specific evaluation.",
                    method="comparison",
                    method_version="1",
                    created_at=f"2026-09-18T00:00:{12 + second_offset:02d}Z",
                )
            )

        assert discover_evaluation_tensions(store, "2026-09-18T00:00:14Z") == ()


def test_transformation_preserves_translation_lineage():
    from episteme import Transformation

    source = make_record(
        RecordKind.SOURCE,
        {"external_format": "example", "value": "raw"},
        (provenance(),),
        "2026-09-18T00:00:01Z",
    )
    output = make_record(
        RecordKind.DATASET,
        {"value": "canonical"},
        (provenance(),),
        "2026-09-18T00:00:02Z",
    )
    transformation = Transformation(
        id="bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
        input_ids=(source.id,),
        operation="example-source-to-canonical",
        operation_version="1",
        assumptions=("source field value is represented verbatim",),
        output_ids=(output.id,),
        executed_at="2026-09-18T00:00:03Z",
        validation_result="passed",
        provenance=(provenance(),),
    )

    with Store() as store:
        store.put_record(source)
        store.put_record(output)
        store.put_transformation(transformation)
        restored = store.get_transformation(transformation.id)

    assert restored == transformation
    assert restored is not None
    assert restored.input_ids == (source.id,)
    assert restored.output_ids == (output.id,)
    assert restored.operation == "example-source-to-canonical"
    assert restored.operation_version == "1"
    assert restored.assumptions == ("source field value is represented verbatim",)
    assert restored.validation_result == "passed"
    assert restored.provenance == (provenance(),)


def test_phase11_accepts_two_distinct_finite_source_representations(tmp_path):
    from episteme import ingest_jsonl_file
    from episteme.public_import import import_crossref_works

    jsonl = tmp_path / "source.jsonl"
    jsonl.write_text(
        '{"id":"cccccccc-cccc-4ccc-8ccc-cccccccccccc","kind":"source","payload":{"external_format":"jsonl-source","content":"finite source material"},"provenance":[{"source_id":"finite:jsonl","source_location":"urn:finite:jsonl","source_version":"1","captured_at":"2026-09-18T00:00:00Z"}],"created_at":"2026-09-18T00:00:00Z","schema_version":1}\n',
        encoding="utf-8",
    )
    crossref = {
        "message": {
            "items": [{
                "DOI": "10.1234/phase11.1",
                "title": ["Finite source material"],
                "type": "journal-article",
            }]
        }
    }

    with Store() as store:
        assert ingest_jsonl_file(jsonl, store) == 1
        assert import_crossref_works(
            crossref,
            store,
            captured_at="2026-09-18T00:00:01Z",
        ) == 1
        records = list(store.iter_records())

    assert len(records) == 2
    assert {record.payload["external_format"] for record in records} == {
        "jsonl-source",
        "crossref-work",
    }
    assert {record.provenance[0].source_id for record in records} == {
        "finite:jsonl",
        "crossref:10.1234/phase11.1",
    }
