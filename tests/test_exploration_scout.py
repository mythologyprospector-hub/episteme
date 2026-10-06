"""Proof of the bounded exploration scouting boundary."""

import pytest

from episteme import Provenance, Record, RecordKind, Store
from episteme.exploration import scout_positional_records


CREATED = "2026-09-30T00:00:00Z"
PROV = (
    Provenance(
        source_id="scout-fixture",
        captured_at=CREATED,
        source_location="https://example.org/scout",
        source_version="1",
    ),
)
RID1 = "11111111-1111-4111-8111-111111111111"
RID2 = "22222222-2222-4222-8222-222222222222"
RID3 = "33333333-3333-4333-8333-333333333333"


def _seed(path):
    with Store(path) as store:
        for record_id, position in ((RID1, 1), (RID2, 4), (RID3, 2)):
            store.put_record(
                Record(
                    record_id,
                    RecordKind.OBSERVATION,
                    {"position": position},
                    PROV,
                    CREATED,
                )
            )


def test_scout_persists_bounded_generated_observation(tmp_path):
    path = tmp_path / "scout.sqlite"
    _seed(path)

    with Store(path) as store:
        observation = scout_positional_records(
            store,
            (RID1, RID2, RID3),
            "position",
            max_records=3,
            created_at=CREATED,
        )

        assert observation.input_ids == (RID1, RID2, RID3)
        assert observation.method == "bounded-positional-scout"
        assert "1.0" in observation.observation
        assert "2.0" in observation.observation
        assert "4.0" in observation.observation
        assert observation.parameters["max_records"] == 3
        assert store.get_exploration_observation(observation.id) == observation
        assert store.get_record(observation.id) is None
        assert list(store.iter_discovery_findings()) == []


def test_scout_does_not_infer_a_gap(tmp_path):
    path = tmp_path / "scout.sqlite"
    _seed(path)

    with Store(path) as store:
        observation = scout_positional_records(
            store,
            (RID1, RID2),
            "position",
            max_records=2,
            created_at=CREATED,
        )
        assert "gap" not in observation.observation.lower()
        assert "external" in observation.uncertainty.lower()


@pytest.mark.parametrize(
    ("record_ids", "max_records", "match"),
    [
        ((), 1, "at least one record"),
        ((RID1, RID2), 1, "exceed"),
    ],
)
def test_scout_enforces_bounds(tmp_path, record_ids, max_records, match):
    path = tmp_path / "scout.sqlite"
    _seed(path)

    with Store(path) as store:
        with pytest.raises(ValueError, match=match):
            scout_positional_records(
                store,
                record_ids,
                "position",
                max_records=max_records,
                created_at=CREATED,
            )


def test_scout_rejects_missing_or_non_numeric_inputs(tmp_path):
    path = tmp_path / "scout.sqlite"
    _seed(path)

    with Store(path) as store:
        with pytest.raises(ValueError, match="record not found"):
            scout_positional_records(
                store,
                ("44444444-4444-4444-8444-444444444444",),
                "position",
                max_records=1,
                created_at=CREATED,
            )

        store.put_record(
            Record(
                "55555555-5555-4555-8555-555555555555",
                RecordKind.OBSERVATION,
                {"position": "unknown"},
                PROV,
                CREATED,
            )
        )
        with pytest.raises(ValueError, match="finite numeric"):
            scout_positional_records(
                store,
                ("55555555-5555-4555-8555-555555555555",),
                "position",
                max_records=1,
                created_at=CREATED,
            )
