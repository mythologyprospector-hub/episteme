"""Tests for the Biology domain boundary."""

import pytest

from episteme.domains.biology import (
    BIOLOGY_DOMAIN,
    BIOLOGY_SCHEMA,
    make_biology_observation,
    validate_observation,
)
from episteme.model import Provenance, RecordKind
from episteme.store import Store


def _provenance():
    return (
        Provenance(
            source_id="biology-fixture",
            source_location="https://example.org/study",
            source_version="1",
            captured_at="2026-09-18T00:00:00+00:00",
        ),
    )


def test_translation_produces_grounded_observation():
    record = make_biology_observation(
        {
            "observation": {"phenotype": "striped", "present": True},
            "subject": "specimen-1",
            "trial": "trial-1",
            "conditions": {"temperature_c": 25, "medium": "control"},
        },
        _provenance(),
        "2026-09-18T00:01:00+00:00",
    )

    assert record.kind is RecordKind.OBSERVATION
    assert record.payload["domain"] == BIOLOGY_DOMAIN
    assert record.payload["schema"] == BIOLOGY_SCHEMA
    assert record.payload["data"]["observation"]["phenotype"] == "striped"


def test_categorical_and_structured_observation_need_not_be_numeric():
    record = make_biology_observation(
        {
            "observation": {
                "growth": "present",
                "morphology": {"shape": "rod", "motility": False},
            }
        },
        _provenance(),
        "2026-09-18T00:01:00+00:00",
    )

    assert record.payload["data"]["observation"]["morphology"]["shape"] == "rod"


@pytest.mark.parametrize("status", ["not_observed", "not_reported", "unresolved"])
def test_missing_information_remains_explicit(status):
    payload = {"observation": {}, "status": status}

    validate_observation(payload)

    record = make_biology_observation(
        payload,
        _provenance(),
        "2026-09-18T00:01:00+00:00",
    )

    assert record.payload["data"]["status"] == status
    assert record.payload["data"]["observation"] == {}


def test_non_observed_status_cannot_hide_observation_data():
    with pytest.raises(ValueError):
        validate_observation(
            {
                "observation": {"phenotype": "striped"},
                "status": "not_reported",
            }
        )


def test_provenance_is_preserved_unchanged():
    provenance = _provenance()
    record = make_biology_observation(
        {"observation": {"phenotype": "striped"}},
        provenance,
        "2026-09-18T00:01:00+00:00",
    )

    assert record.provenance == provenance


def test_repeated_trials_remain_distinct_grounded_records():
    first = make_biology_observation(
        {
            "observation": {"growth": "present"},
            "subject": "specimen-1",
            "trial": "trial-1",
        },
        _provenance(),
        "2026-09-18T00:01:00+00:00",
    )
    second = make_biology_observation(
        {
            "observation": {"growth": "absent"},
            "subject": "specimen-1",
            "trial": "trial-2",
        },
        _provenance(),
        "2026-09-18T00:02:00+00:00",
    )

    assert first.id != second.id
    assert first.kind is RecordKind.OBSERVATION
    assert second.kind is RecordKind.OBSERVATION
    assert first.payload["data"]["trial"] != second.payload["data"]["trial"]


def test_conflicting_observations_are_not_reconciled():
    first = make_biology_observation(
        {"observation": {"expression": "high"}, "subject": "sample-1"},
        _provenance(),
        "2026-09-18T00:01:00+00:00",
    )
    second = make_biology_observation(
        {"observation": {"expression": "low"}, "subject": "sample-1"},
        _provenance(),
        "2026-09-18T00:02:00+00:00",
    )

    assert first.payload["data"]["observation"] != second.payload["data"]["observation"]
    assert first.id != second.id


def test_core_store_round_trip_keeps_domain_payload():
    store = Store(":memory:")
    record = make_biology_observation(
        {
            "observation": {"phenotype": "striped"},
            "conditions": {"light": "12h"},
        },
        _provenance(),
        "2026-09-18T00:01:00+00:00",
    )

    store.add_record(record)
    loaded = store.get_record(record.id)

    assert loaded == record
    assert loaded.kind is RecordKind.OBSERVATION
    assert loaded.payload["domain"] == BIOLOGY_DOMAIN


def test_translation_is_deterministic_for_equivalent_structure():
    first = make_biology_observation(
        {
            "observation": {"phenotype": "striped", "present": True},
            "conditions": {"temperature": 25, "medium": "control"},
        },
        _provenance(),
        "2026-09-18T00:01:00+00:00",
    )
    second = make_biology_observation(
        {
            "conditions": {"medium": "control", "temperature": 25},
            "observation": {"present": True, "phenotype": "striped"},
        },
        _provenance(),
        "2026-09-18T00:01:00+00:00",
    )

    assert first.payload == second.payload
