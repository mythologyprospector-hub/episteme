from episteme import (
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
            assert "missing record" in str(exc)
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
    assert finding.expectation == (first.id, "related_to", second.id)


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
    assert restored.expectation == (first.id, "related_to", second.id)


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
    assert restored[0].expectation == (first.id, "related_to", second.id)



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
            expectation=(first, "contradicts", second),
        )
    except ValueError as exc:
        assert "only gap and unresolved-question findings" in str(exc)
    else:
        raise AssertionError("non-gap finding accepted an expectation")
