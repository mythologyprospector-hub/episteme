"""Proof of the durable exploration-observation discovery boundary."""

import pytest

from episteme import (
    ExplorationObservation,
    Provenance,
    Record,
    RecordKind,
    Store,
    admit_exploration_observation,
    assess_exploration_observation,
)


CREATED = "2026-09-30T00:00:00Z"
PROV = (
    Provenance(
        source_id="exploration-fixture",
        captured_at=CREATED,
        source_location="https://example.org/exploration",
        source_version="1",
    ),
)
RID = "77777777-7777-4777-8777-777777777777"
OID = "88888888-8888-4888-8888-888888888888"
AID = "99999999-9999-4999-8999-999999999999"


def _seed(path):
    with Store(path) as store:
        record = Record(OID, RecordKind.SOURCE, {"title": "fixture"}, PROV, CREATED)
        observation = ExplorationObservation(
            id=RID,
            observation="A supplied record is represented in the exploration corpus.",
            input_ids=(OID,),
            evidence=("The source record is explicitly present in the supplied corpus.",),
            method="fixture-observation",
            method_version="1",
            uncertainty="This is generated observation, not an established relationship.",
            parameters={"model": "fixture"},
            created_at=CREATED,
        )
        store.put_record(record)
        store.put_exploration_observation(observation)
    return observation


def _assessment(store, *, accepted: bool, observation_id: str = RID):
    return assess_exploration_observation(
        store,
        observation_id,
        accepted=accepted,
        method="fixture-assessment",
        method_version="1",
        rationale="The fixture assessment is explicit and deterministic.",
        provenance=PROV,
        assessed_at=CREATED,
    )


def test_assessment_is_durable_and_does_not_change_observation(tmp_path):
    path = tmp_path / "exploration.sqlite"
    observation = _seed(path)

    with Store(path) as store:
        assessment = _assessment(store, accepted=True)
        assert assessment.observation_id == observation.id
        assert store.get_exploration_observation(observation.id) == observation
        assert store.get_exploration_observation_assessment(assessment.id) == assessment
        assert list(store.iter_exploration_observation_assessments()) == [assessment]

    with Store(path, read_only=True) as store:
        assert store.get_exploration_observation(observation.id) == observation
        assert store.get_exploration_observation_assessment(assessment.id) == assessment


def test_assessment_requires_existing_observation(tmp_path):
    with Store(tmp_path / "exploration.sqlite") as store:
        with pytest.raises(ValueError, match="exploration observation not found"):
            _assessment(store, accepted=True)


def test_accepted_observation_enters_discovery_as_generated_context(tmp_path):
    path = tmp_path / "exploration.sqlite"
    observation = _seed(path)

    with Store(path) as store:
        assessment = _assessment(store, accepted=True)
        finding = admit_exploration_observation(
            store,
            observation.id,
            assessment.id,
            CREATED,
        )

        assert finding.kind.value == "exploration_observation"
        assert finding.input_ids == observation.input_ids
        assert observation.id in finding.context_ids
        assert assessment.id in finding.context_ids
        assert store.get_record(observation.id) is None
        assert store.get_discovery_finding(finding.id) == finding


def test_rejected_observation_cannot_enter_discovery(tmp_path):
    path = tmp_path / "exploration.sqlite"
    observation = _seed(path)

    with Store(path) as store:
        assessment = _assessment(store, accepted=False)
        with pytest.raises(ValueError, match="rejected exploration observation"):
            admit_exploration_observation(
                store,
                observation.id,
                assessment.id,
                CREATED,
            )
        assert list(store.iter_discovery_findings()) == []


def test_mismatched_assessment_cannot_enter_discovery(tmp_path):
    path = tmp_path / "exploration.sqlite"
    first = _seed(path)

    with Store(path) as store:
        second = ExplorationObservation(
            id=AID,
            observation="A second generated observation.",
            input_ids=(OID,),
            evidence=("The same grounded source remains represented.",),
            method="fixture-observation",
            method_version="1",
            uncertainty="Generated and uncertain.",
            parameters=None,
            created_at=CREATED,
        )
        store.put_exploration_observation(second)
        assessment = _assessment(store, accepted=True, observation_id=first.id)

        with pytest.raises(ValueError, match="does not reference"):
            admit_exploration_observation(
                store,
                second.id,
                assessment.id,
                CREATED,
            )
