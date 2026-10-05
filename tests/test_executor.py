from episteme.executor import PositionalObservationExecutor
from episteme.model import Provenance, Record, RecordKind
from episteme.proposals import propose_experiment, predict, propose_hypothesis
from episteme.store import Store

CREATED = "2026-10-05T00:00:00Z"
PROVENANCE = (
    Provenance(
        source_id="executor-fixture",
        captured_at=CREATED,
        source_location="https://example.org/executor",
        source_version="1",
    ),
)


def _record(index: int, position: float) -> Record:
    return Record(
        id=f"bbbbbbbb-{index:04d}-4aaa-8aaa-bbbbbbbbbbbb",
        kind=RecordKind.OBSERVATION,
        payload={"position": position},
        provenance=PROVENANCE,
        created_at=CREATED,
    )


def test_positional_executor_records_a_real_result():
    records = (_record(1, 4.0), _record(2, 1.0), _record(3, 2.0))

    with Store() as store:
        for record in records:
            store.put_record(record)

        hypothesis_ids = []
        for statement in ("position 3.0 is occupied", "position 3.0 is absent"):
            hypothesis = propose_hypothesis(
                statement=statement,
                finding_ids=(),
                input_ids=tuple(record.id for record in records),
                method="fixture",
                method_version="1",
                rationale="fixture",
                created_at=CREATED,
            )
            # Hypothesis requires a finding; this test only needs real proposal
            # persistence, so the executor test creates the hypotheses elsewhere.
            hypothesis_ids.append(hypothesis)

        # Use the model constructors directly for this focused executor test.
        from episteme.model import Hypothesis
        hypotheses = tuple(
            Hypothesis(
                id=item.id,
                statement=item.statement,
                finding_ids=(str(__import__("uuid").uuid4()),),
                input_ids=item.input_ids,
                method=item.method,
                method_version=item.method_version,
                rationale=item.rationale,
                assumptions=item.assumptions,
                created_at=item.created_at,
            )
            for item in hypothesis_ids
        )
        # The executor only needs a persisted experiment proposal. Seed its
        # dependency tables with minimal valid objects.
        from episteme.model import DiscoveryFinding, DiscoveryFindingKind
        finding = DiscoveryFinding(
            id=hypotheses[0].finding_ids[0],
            kind=DiscoveryFindingKind.GAP,
            title="fixture gap",
            description="fixture gap",
            input_ids=tuple(record.id for record in records),
            method="fixture",
            method_version="1",
            rationale="fixture",
            measures=(),
            created_at=CREATED,
        )
        store.put_discovery_finding(finding)
        for hypothesis in hypotheses:
            store.put_hypothesis(hypothesis)

        predictions = []
        for hypothesis in hypotheses:
            prediction = predict(
                source_id=hypothesis.id,
                consequence="measure the represented positions",
                conditions="same observations",
                method="fixture",
                method_version="1",
                rationale="fixture",
                comparison_hypothesis_ids=tuple(item.id for item in hypotheses),
                created_at=CREATED,
            )
            store.put_prediction(prediction)
            predictions.append(prediction)

        proposal = propose_experiment(
            prediction_ids=tuple(item.id for item in predictions),
            objective="measure the represented positions",
            proposed_observation="the observed positions",
            discrimination_basis="the recorded positions are the empirical result",
            conditions="same observations",
            method="fixture",
            method_version="1",
            rationale="fixture",
            created_at=CREATED,
        )
        store.put_experiment_proposal(proposal)

        result = PositionalObservationExecutor().execute(
            store,
            proposal,
            input_ids=tuple(record.id for record in records),
            created_at=CREATED,
        )

        assert result.kind is RecordKind.RESULT
        assert result.payload["observed_positions"] == [1.0, 2.0, 4.0]
        assert result.payload["experiment_proposal_id"] == proposal.id
        assert store.get_record(result.id) == result
