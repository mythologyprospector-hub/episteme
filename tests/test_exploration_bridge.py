from episteme.exploration_bridge import assess_exploration_observation
from episteme.model import ExplorationObservation, Provenance, Record, RecordKind
from episteme.store import Store

CREATED = "2026-10-05T00:00:00Z"


def test_assessment_references_observation_without_promoting_it():
    observation = ExplorationObservation(
        id="11111111-1111-4111-8111-111111111111",
        observation="A generated scouting observation.",
        input_ids=("22222222-2222-4222-8222-222222222222",),
        evidence=("derived measurement",),
        method="fixture-scout",
        method_version="1",
        uncertainty="medium",
        created_at=CREATED,
    )
    with Store() as store:
        store.put_record(
            Record(
                id=observation.input_ids[0],
                kind=RecordKind.OBSERVATION,
                payload={"position": 3.0},
                provenance=(
                    Provenance(
                        source_id="fixture",
                        captured_at=CREATED,
                        source_location="https://example.org/fixture",
                    ),
                ),
                created_at=CREATED,
            )
        )
        store.put_exploration_observation(observation)
        assessment = assess_exploration_observation(
            store,
            observation.id,
            method="fixture-assessment",
            rationale="Assessment is explicit and does not change epistemic status.",
        )

        assert assessment.observation_id == observation.id
        assert assessment.accepted is True
        assert store.get_exploration_observation(observation.id) == observation
        assert store.get_record(observation.id) is None


def test_assessment_rejects_missing_observation():
    with Store() as store:
        try:
            assess_exploration_observation(
                store,
                "33333333-3333-4333-8333-333333333333",
                method="fixture-assessment",
                rationale="No such observation.",
            )
        except ValueError as exc:
            assert "does not exist" in str(exc)
        else:
            raise AssertionError("missing observation was accepted")
