"""Tests for the read-only public Episteme instrument."""

from episteme import (
    Relationship,
    DiscoveryFinding,
    DiscoveryFindingKind,
    DiscoveryMeasure,
    ExperimentProposal,
    Hypothesis,
    KnowledgeStateConsequence,
    KnowledgeStateConsequenceKind,
    KnowledgeStateTargetKind,
    Prediction,
    PredictionEvaluation,
    PredictionEvaluationOutcome,
    Provenance,
    RecordKind,
    Store,
    discovery_lineage,
    discovery_report,
    discovery_trail,
    get_record,
    get_review,
    list_records,
    list_reviews,
    make_record,
)


CREATED = "2026-09-18T00:00:00Z"
PROVENANCE = (
    Provenance(
        source_id="public-test",
        captured_at=CREATED,
        source_location="https://example.org/public-test",
        source_version="1",
    ),
)


def test_public_api_reads_grounded_records_without_changing_them():
    record = make_record(
        kind=RecordKind.OBSERVATION,
        payload={"value": "fixture"},
        provenance=PROVENANCE,
        created_at=CREATED,
    )

    with Store() as store:
        store.put_record(record)
        before = record.to_dict()

        assert get_record(store, record.id) == before
        assert list_records(store) == [before]
        assert record.to_dict() == before


def test_public_api_exposes_trail_and_report_without_reinterpreting_state():
    record = make_record(
        kind=RecordKind.OBSERVATION,
        payload={"value": "fixture"},
        provenance=PROVENANCE,
        created_at=CREATED,
    )
    finding = DiscoveryFinding(
        id="66666666-6666-4666-8666-666666666666",
        kind=DiscoveryFindingKind.TENSION,
        title="Public inspection fixture",
        description="A deterministic finding used to exercise the public surface.",
        input_ids=(record.id,),
        method="public-test",
        method_version="1",
        rationale="Test fixture only.",
        measures=(
            DiscoveryMeasure(
                name="input_count",
                value=1.0,
                scale="count",
                basis="one grounded fixture record",
            ),
        ),
        created_at=CREATED,
    )

    with Store() as store:
        store.put_record(record)
        store.put_discovery_finding(finding)

        trail = discovery_trail(store, finding.id, "2026-09-18T00:01:00Z")
        lineage = discovery_lineage(store, finding.id, "2026-09-18T00:01:00Z")
        report = discovery_report(store, finding.id, "2026-09-18T00:01:00Z")

    assert trail["finding_id"] == finding.id
    assert lineage["finding_id"] == finding.id
    assert "created_at" not in lineage
    assert report["report"] == "episteme-discovery-report-v1"
    assert report["grounded_records"][0]["id"] == record.id
    assert report["generated_artifacts"][0]["id"] == finding.id
    assert report["lineage"] == lineage



def test_public_report_keeps_grounded_relationships_grounded():
    subject = make_record(kind=RecordKind.OBSERVATION, payload={"value": "subject"}, provenance=PROVENANCE, created_at=CREATED)
    object_record = make_record(kind=RecordKind.OBSERVATION, payload={"value": "object"}, provenance=PROVENANCE, created_at=CREATED)
    relationship = Relationship(id="88888888-8888-4888-8888-888888888881", subject_id=subject.id, predicate="contradicts", object_id=object_record.id, provenance=PROVENANCE, created_at=CREATED)
    finding = DiscoveryFinding(id="88888888-8888-4888-8888-888888888882", kind=DiscoveryFindingKind.CONTRADICTION, title="Grounded relationship fixture", description="The relationship is grounded input to discovery.", input_ids=(relationship.id, subject.id, object_record.id), method="public-test", method_version="1", rationale="Test fixture only.", measures=(), created_at=CREATED)
    with Store() as store:
        store.put_record(subject)
        store.put_record(object_record)
        store.put_relationship(relationship)
        store.put_discovery_finding(finding)
        report = discovery_report(store, finding.id, CREATED)
    grounded_kinds = {entry["kind"] for entry in report["grounded_records"]}
    generated_kinds = {entry["kind"] for entry in report["generated_artifacts"]}
    assert "relationship" in grounded_kinds
    assert "relationship" not in generated_kinds


def test_cli_records_reads_a_store(tmp_path, capsys):
    record = make_record(
        kind=RecordKind.OBSERVATION,
        payload={"value": "cli-fixture"},
        provenance=PROVENANCE,
        created_at=CREATED,
    )
    store_path = tmp_path / "episteme.sqlite"
    with Store(store_path) as store:
        store.put_record(record)

    from episteme.__main__ import main

    import sys
    original = sys.argv
    try:
        sys.argv = ["python -m episteme", "--store", str(store_path), "records"]
        assert main() == 0
    finally:
        sys.argv = original

    import json
    assert json.loads(capsys.readouterr().out) == [record.to_dict()]


def test_public_report_reconstructs_a_complete_discovery_cycle():
    initial = make_record(
        kind=RecordKind.OBSERVATION,
        payload={"value": "initial-observation"},
        provenance=PROVENANCE,
        created_at=CREATED,
    )
    result = make_record(
        kind=RecordKind.RESULT,
        payload={"value": "observed-result"},
        provenance=PROVENANCE,
        created_at=CREATED,
    )
    finding_id = "66666666-6666-4666-8666-666666666661"
    hypothesis_id = "66666666-6666-4666-8666-666666666662"
    prediction_id = "66666666-6666-4666-8666-666666666663"
    proposal_id = "66666666-6666-4666-8666-666666666664"
    evaluation_id = "66666666-6666-4666-8666-666666666665"
    consequence_id = "66666666-6666-4666-8666-666666666666"
    final_finding_id = "66666666-6666-4666-8666-666666666667"

    finding = DiscoveryFinding(
        id=finding_id,
        kind=DiscoveryFindingKind.TENSION,
        title="Cycle starting point",
        description="A bounded starting finding.",
        input_ids=(initial.id,),
        method="public-cycle-test",
        method_version="1",
        rationale="Test fixture only.",
        measures=(),
        created_at=CREATED,
    )
    hypothesis = Hypothesis(
        id=hypothesis_id,
        statement="The observed condition has the proposed cause.",
        finding_ids=(finding.id,),
        input_ids=(initial.id,),
        method="public-cycle-test",
        method_version="1",
        rationale="Test fixture only.",
        assumptions=("fixture assumption",),
        created_at=CREATED,
    )
    prediction = Prediction(
        id=prediction_id,
        source_id=hypothesis.id,
        consequence="The proposed measurement will be observed.",
        conditions="Fixture conditions.",
        assumptions=("fixture assumption",),
        method="public-cycle-test",
        method_version="1",
        rationale="Test fixture only.",
        comparison_hypothesis_ids=(),
        created_at=CREATED,
    )
    proposal = ExperimentProposal(
        id=proposal_id,
        prediction_ids=(prediction.id,),
        objective="Test the prediction.",
        proposed_observation="Measure the fixture result.",
        discrimination_basis="The observation distinguishes the proposed consequence.",
        conditions="Fixture conditions.",
        assumptions=("fixture assumption",),
        method="public-cycle-test",
        method_version="1",
        rationale="Test fixture only.",
        created_at=CREATED,
    )
    evaluation = PredictionEvaluation(
        id=evaluation_id,
        result_id=result.id,
        prediction_id=prediction.id,
        experiment_proposal_id=proposal.id,
        comparison_conditions="Fixture conditions.",
        assumptions=("fixture assumption",),
        outcome=PredictionEvaluationOutcome.CONSISTENT,
        rationale="The observed result matches the stated prediction under the fixture conditions.",
        method="public-cycle-test",
        method_version="1",
        created_at=CREATED,
    )
    consequence = KnowledgeStateConsequence(
        id=consequence_id,
        evaluation_ids=(evaluation.id,),
        target_kind=KnowledgeStateTargetKind.HYPOTHESIS,
        target_id=hypothesis.id,
        consequence=KnowledgeStateConsequenceKind.SUPPORTS,
        assumptions=("fixture assumption",),
        rationale="Fixture consequence only.",
        method="public-cycle-test",
        method_version="1",
        created_at=CREATED,
    )
    final_finding = DiscoveryFinding(
        id=final_finding_id,
        kind=DiscoveryFindingKind.TENSION,
        title="Cycle continuation",
        description="A finding generated from the evaluated result.",
        input_ids=(result.id,),
        context_ids=(consequence.id,),
        method="public-cycle-test",
        method_version="1",
        rationale="Test fixture only.",
        measures=(),
        created_at=CREATED,
    )

    with Store() as store:
        store.put_record(initial)
        store.put_discovery_finding(finding)
        store.put_hypothesis(hypothesis)
        store.put_prediction(prediction)
        store.put_experiment_proposal(proposal)
        store.put_record(result)
        store.put_prediction_evaluation(evaluation)
        store.put_knowledge_state_consequence(consequence)
        store.put_discovery_finding(final_finding)

        report = discovery_report(store, final_finding.id, "2026-09-18T00:01:00Z")

    kinds = {entry["kind"] for entry in report["trail"]["entries"]}
    assert {
        "record",
        "discovery_finding",
        "hypothesis",
        "prediction",
        "experiment_proposal",
        "prediction_evaluation",
        "knowledge_state_consequence",
    } <= kinds
    assert report["grounded_records"]
    assert report["generated_artifacts"]
    assert any(entry["id"] == initial.id for entry in report["grounded_records"])
    assert any(entry["id"] == result.id for entry in report["grounded_records"])
    assert report["lineage"]["finding_id"] == final_finding.id
    assert "created_at" not in report["lineage"]



def test_review_is_immutable_and_does_not_mutate_target():
    record = make_record(
        kind=RecordKind.OBSERVATION,
        payload={"value": "review-target"},
        provenance=PROVENANCE,
        created_at=CREATED,
    )
    from episteme import Review, ReviewDisposition, ReviewTargetKind

    review = Review(
        id="77777777-7777-4777-8777-777777777771",
        target_kind=ReviewTargetKind.RECORD,
        target_id=record.id,
        reviewer="researcher@example",
        disposition=ReviewDisposition.CHALLENGE,
        basis="The observation requires clarification.",
        rationale="The supplied context is insufficient to reproduce the observation.",
        provenance=PROVENANCE,
        reviewed_at=CREATED,
    )

    with Store() as store:
        store.put_record(record)
        before = record.to_dict()
        store.put_review(review)

        assert store.get_review(review.id).to_dict() == review.to_dict()
        assert list(store.iter_reviews(record.id))[0].id == review.id
        assert store.get_record(record.id).to_dict() == before


def test_multiple_reviews_preserve_disagreement():
    record = make_record(
        kind=RecordKind.OBSERVATION,
        payload={"value": "disputed"},
        provenance=PROVENANCE,
        created_at=CREATED,
    )
    from episteme import Review, ReviewDisposition, ReviewTargetKind

    reviews = (
        Review(
            id="77777777-7777-4777-8777-777777777772",
            target_kind=ReviewTargetKind.RECORD,
            target_id=record.id,
            reviewer="reviewer-a",
            disposition=ReviewDisposition.ACKNOWLEDGE,
            basis="The supplied record is internally clear.",
            rationale="No issue found in the represented material.",
            provenance=PROVENANCE,
            reviewed_at=CREATED,
        ),
        Review(
            id="77777777-7777-4777-8777-777777777773",
            target_kind=ReviewTargetKind.RECORD,
            target_id=record.id,
            reviewer="reviewer-b",
            disposition=ReviewDisposition.CHALLENGE,
            basis="The supplied record lacks needed context.",
            rationale="Additional context is required before relying on it.",
            provenance=PROVENANCE,
            reviewed_at="2026-09-18T00:01:00Z",
        ),
    )

    with Store() as store:
        store.put_record(record)
        for review in reviews:
            store.put_review(review)

        assert [item.disposition.value for item in store.iter_reviews(record.id)] == [
            "acknowledge",
            "challenge",
        ]


def test_review_rejects_missing_target_without_creating_state():
    from episteme import Review, ReviewDisposition, ReviewTargetKind

    review = Review(
        id="77777777-7777-4777-8777-777777777774",
        target_kind=ReviewTargetKind.RECORD,
        target_id="77777777-7777-4777-8777-777777777775",
        reviewer="reviewer",
        disposition=ReviewDisposition.NOTE,
        basis="Inspection basis.",
        rationale="Target does not exist.",
        provenance=PROVENANCE,
        reviewed_at=CREATED,
    )

    with Store() as store:
        try:
            store.put_review(review)
        except ValueError as exc:
            assert "references missing record" in str(exc)
        else:
            raise AssertionError("missing review target should be rejected")
        assert list(store.iter_reviews()) == []


def test_public_review_api_scopes_by_target_kind_and_id():
    from episteme import Review, ReviewDisposition, ReviewTargetKind

    record = make_record(
        kind=RecordKind.OBSERVATION,
        payload={"value": "public-review"},
        provenance=PROVENANCE,
        created_at=CREATED,
    )
    review = Review(
        id="77777777-7777-4777-8777-777777777776",
        target_kind=ReviewTargetKind.RECORD,
        target_id=record.id,
        reviewer="public-reviewer",
        disposition=ReviewDisposition.NOTE,
        basis="Public inspection test.",
        rationale="The review is represented without changing the record.",
        provenance=PROVENANCE,
        reviewed_at=CREATED,
    )

    with Store() as store:
        store.put_record(record)
        store.put_review(review)

        assert get_review(store, review.id) == review.to_dict()
        assert list_reviews(store) == [review.to_dict()]
        assert list_reviews(store, target_kind=ReviewTargetKind.RECORD, target_id=record.id) == [review.to_dict()]
        assert list_reviews(store, target_kind=ReviewTargetKind.HYPOTHESIS, target_id=record.id) == []
