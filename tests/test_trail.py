from episteme import (
    DiscoveryExpectation,
    DiscoveryExpectationKind,
    DiscoveryFinding,
    DiscoveryFindingKind,
    DiscoveryMeasure,
    PredictionEvaluation,
    PredictionEvaluationOutcome,
    Provenance,
    Record,
    RecordKind,
    Store,
    build_discovery_trail,
    propose_experiment,
    propose_hypothesis,
    predict,
)


def p(source: str = "source-a") -> Provenance:
    return Provenance(source_id=source, captured_at="2026-09-18T00:00:00Z")


def record(identifier: str, kind: RecordKind, payload: dict) -> Record:
    return Record(
        id=identifier,
        kind=kind,
        payload=payload,
        provenance=(p(),),
        created_at="2026-09-18T00:00:00Z",
    )


def finding(identifier: str, input_id: str) -> DiscoveryFinding:
    return DiscoveryFinding(
        id=identifier,
        kind=DiscoveryFindingKind.GAP,
        title="Expected relationship is not represented",
        description="A bounded expected relationship is absent.",
        input_ids=(input_id,),
        method="test",
        method_version="1",
        rationale="Explicit test expectation.",
        measures=(
            DiscoveryMeasure(
                name="input_count",
                value=1.0,
                scale="count",
                basis="test",
            ),
        ),
        created_at="2026-09-18T00:00:00Z",
        expectation=DiscoveryExpectation(DiscoveryExpectationKind.RELATIONSHIP, {"subject_id": input_id, "predicate": "expects", "object_id": input_id}),
    )


def test_discovery_trail_reconstructs_closed_loop_deterministically():
    grounded = record(
        "11111111-1111-4111-8111-111111111111",
        RecordKind.OBSERVATION,
        {"name": "observation"},
    )
    result = record(
        "22222222-2222-4222-8222-222222222222",
        RecordKind.RESULT,
        {"observed": "outcome"},
    )
    origin = finding("33333333-3333-4333-8333-333333333333", grounded.id)

    with Store() as store:
        store.put_record(grounded)
        store.put_record(result)
        store.put_discovery_finding(origin)

        hypothesis = propose_hypothesis(
            statement="Explanation.",
            finding_ids=(origin.id,),
            method="test",
            method_version="1",
            rationale="Generated candidate.",
            created_at="2026-09-18T00:00:01Z",
        )
        store.put_hypothesis(hypothesis)

        prediction = predict(
            source_id=hypothesis.id,
            consequence="Outcome.",
            conditions="Condition.",
            method="test",
            method_version="1",
            rationale="Generated prediction.",
            created_at="2026-09-18T00:00:02Z",
        )
        store.put_prediction(prediction)

        proposal = propose_experiment(
            prediction_ids=(prediction.id,),
            objective="Test prediction.",
            proposed_observation="Measure outcome.",
            discrimination_basis="Outcome can distinguish the prediction.",
            conditions="Condition.",
            assumptions=(),
            method="test",
            method_version="1",
            rationale="Generated proposal.",
            created_at="2026-09-18T00:00:03Z",
        )
        store.put_experiment_proposal(proposal)

        evaluation = PredictionEvaluation(
            id="44444444-4444-4444-8444-444444444444",
            result_id=result.id,
            prediction_id=prediction.id,
            experiment_proposal_id=proposal.id,
            comparison_conditions="Condition.",
            assumptions=(),
            outcome=PredictionEvaluationOutcome.CONSISTENT,
            rationale="Compatible.",
            method="comparison",
            method_version="1",
            created_at="2026-09-18T00:00:05Z",
        )
        store.put_prediction_evaluation(evaluation)

        renewed = DiscoveryFinding(
            id="55555555-5555-4555-8555-555555555555",
            kind=DiscoveryFindingKind.TENSION,
            title="Renewed finding",
            description="Differing evaluations require renewed inspection.",
            input_ids=(result.id,),
            context_ids=(evaluation.id,),
            method="evaluation-conflict-discovery",
            method_version="1",
            rationale="Test renewed discovery.",
            measures=(
                DiscoveryMeasure(
                    name="input_count",
                    value=1.0,
                    scale="count",
                    basis="test",
                ),
            ),
            created_at="2026-09-18T00:00:06Z",
        )
        store.put_discovery_finding(renewed)

        trail = build_discovery_trail(
            store,
            renewed.id,
            "2026-09-18T00:00:07Z",
        )
        second = build_discovery_trail(
            store,
            renewed.id,
            "2026-09-18T00:00:07Z",
        )
        later = build_discovery_trail(
            store,
            renewed.id,
            "2026-09-18T00:00:08Z",
        )

    assert trail == second
    assert trail.to_json() == second.to_json()
    assert trail.to_lineage_json() == second.to_lineage_json()

    assert trail.to_json() != later.to_json()
    assert trail.to_lineage_json() == later.to_lineage_json()

    kinds = [(entry.kind, entry.id) for entry in trail.entries]
    assert ("discovery_finding", renewed.id) in kinds
    assert ("prediction_evaluation", evaluation.id) in kinds
    assert ("record", result.id) in kinds
    assert ("prediction", prediction.id) in kinds
    assert ("experiment_proposal", proposal.id) in kinds
    assert ("hypothesis", hypothesis.id) in kinds
    assert ("discovery_finding", origin.id) in kinds
    assert ("record", grounded.id) in kinds


def test_discovery_trail_fails_on_missing_root_finding():
    with Store() as store:
        try:
            build_discovery_trail(
                store,
                "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                "2026-09-18T00:00:04Z",
            )
        except ValueError as exc:
            assert "missing finding" in str(exc)
        else:
            raise AssertionError("missing root finding was silently accepted")
