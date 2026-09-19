"""Phase 7 proof that materially different domain records share downstream core machinery."""

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
    predict,
    propose_experiment,
    propose_hypothesis,
)
from episteme.domains.astronomy import make_astronomy_measurement
from episteme.domains.biology import make_biology_observation


CREATED = "2026-09-18T00:00:00Z"
PROVENANCE = (
    Provenance(
        source_id="phase7-fixture",
        captured_at=CREATED,
        source_location="https://example.org/phase7",
        source_version="1",
    ),
)


def test_astronomy_and_biology_share_the_same_closed_loop_core():
    astronomy = make_astronomy_measurement(
        {"quantity": "flux", "value": 2.5, "unit": "Jy", "target": "example-object"},
        PROVENANCE,
        CREATED,
    )
    biology = make_biology_observation(
        {
            "observation": {"phenotype": "striped"},
            "subject": "example-subject",
            "trial": "trial-1",
        },
        PROVENANCE,
        CREATED,
    )
    result = Record(
        id="22222222-2222-4222-8222-222222222222",
        kind=RecordKind.RESULT,
        payload={"observed": "fixture outcome"},
        provenance=PROVENANCE,
        created_at=CREATED,
    )
    origin = DiscoveryFinding(
        id="33333333-3333-4333-8333-333333333333",
        kind=DiscoveryFindingKind.GAP,
        title="Mixed-domain expectation",
        description="A bounded expectation spans two grounded domain records.",
        input_ids=(astronomy.id, biology.id),
        method="phase7-cross-domain-fixture",
        method_version="1",
        rationale="The fixture tests shared core semantics without inventing a scientific relationship.",
        measures=(
            DiscoveryMeasure(
                name="input_count",
                value=2.0,
                scale="count",
                basis="two grounded records from materially different domain adapters",
            ),
        ),
        created_at=CREATED,
        expectation=DiscoveryExpectation(DiscoveryExpectationKind.RELATIONSHIP, {"subject_id": astronomy.id, "predicate": "related_to", "object_id": biology.id}),
    )

    with Store() as store:
        store.put_record(astronomy)
        store.put_record(biology)
        store.put_record(result)
        store.put_discovery_finding(origin)

        hypothesis = propose_hypothesis(
            statement="A generated cross-domain explanation.",
            finding_ids=(origin.id,),
            method="phase7-test",
            method_version="1",
            rationale="Generated only from the discovery finding.",
            created_at="2026-09-18T00:00:01Z",
        )
        store.put_hypothesis(hypothesis)

        prediction = predict(
            source_id=hypothesis.id,
            consequence="The fixture outcome will be observed.",
            conditions="Fixture conditions.",
            method="phase7-test",
            method_version="1",
            rationale="Generated from the hypothesis.",
            created_at="2026-09-18T00:00:02Z",
        )
        store.put_prediction(prediction)

        proposal = propose_experiment(
            prediction_ids=(prediction.id,),
            objective="Test the generated prediction.",
            proposed_observation="Observe the fixture outcome.",
            discrimination_basis="The observation is the proposed test of the prediction.",
            conditions="Fixture conditions.",
            assumptions=(),
            method="phase7-test",
            method_version="1",
            rationale="Generated experiment proposal.",
            created_at="2026-09-18T00:00:03Z",
        )
        store.put_experiment_proposal(proposal)

        evaluation = PredictionEvaluation(
            id="44444444-4444-4444-8444-444444444444",
            result_id=result.id,
            prediction_id=prediction.id,
            experiment_proposal_id=proposal.id,
            comparison_conditions="Fixture conditions.",
            assumptions=(),
            outcome=PredictionEvaluationOutcome.CONSISTENT,
            rationale="Fixture result is compatible with the prediction.",
            method="phase7-test",
            method_version="1",
            created_at="2026-09-18T00:00:04Z",
        )
        store.put_prediction_evaluation(evaluation)

        renewed = DiscoveryFinding(
            id="55555555-5555-4555-8555-555555555555",
            kind=DiscoveryFindingKind.TENSION,
            title="Renewed mixed-domain finding",
            description="The closed-loop lineage returns to discovery.",
            input_ids=(astronomy.id, biology.id, result.id),
            context_ids=(evaluation.id,),
            method="phase7-test",
            method_version="1",
            rationale="The fixture demonstrates renewed discovery over shared core artifacts.",
            measures=(
                DiscoveryMeasure(
                    name="input_count",
                    value=3.0,
                    scale="count",
                    basis="two domain records plus one grounded result",
                ),
            ),
            created_at="2026-09-18T00:00:05Z",
        )
        store.put_discovery_finding(renewed)

        trail = build_discovery_trail(store, renewed.id, "2026-09-18T00:00:06Z")
        later = build_discovery_trail(store, renewed.id, "2026-09-18T00:00:07Z")

    kinds = {(entry.kind, entry.id) for entry in trail.entries}

    assert ("record", astronomy.id) in kinds
    assert ("record", biology.id) in kinds
    assert ("record", result.id) in kinds
    assert ("discovery_finding", origin.id) in kinds
    assert ("hypothesis", hypothesis.id) in kinds
    assert ("prediction", prediction.id) in kinds
    assert ("experiment_proposal", proposal.id) in kinds
    assert ("prediction_evaluation", evaluation.id) in kinds
    assert ("discovery_finding", renewed.id) in kinds
    assert trail.to_lineage_json() == later.to_lineage_json()
    assert trail.to_json() != later.to_json()
