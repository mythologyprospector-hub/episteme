"""Regression test for experiments using held-out evidence.

The discovery phase must not be allowed to answer its own prediction by
re-reading the exact observations that established the gap.
"""

from test_autonomy import AdaptiveFixturePlanner, CREATED, _records

from episteme.autonomy import run_autonomous_discovery
from episteme.discovery import detect_positional_gap
from episteme.model import Provenance, Record, RecordKind
from episteme.store import Store


PROVENANCE = (
    Provenance(
        source_id="fixture://issue2",
        captured_at=CREATED,
        source_location="fixture://issue2",
        source_version="1",
    ),
)


def test_experiment_can_use_host_supplied_held_out_observation():
    """A discriminating experiment must be able to measure data absent from discovery inputs."""

    discovery_records = _records()
    held_out = Record(
        id="eeeeeeee-0001-4aaa-8aaa-eeeeeeeeeeee",
        kind=RecordKind.OBSERVATION,
        payload={"position": 3.0},
        provenance=PROVENANCE,
        created_at=CREATED,
    )

    with Store() as store:
        for record in (*discovery_records, held_out):
            store.put_record(record)

        gap = detect_positional_gap(
            store,
            record_ids=tuple(record.id for record in discovery_records),
            position_key="position",
            step=1.0,
            created_at=CREATED,
        )
        assert gap is not None
        store.put_discovery_finding(gap)

        result = run_autonomous_discovery(
            store,
            AdaptiveFixturePlanner(),
            grounded_input_ids=tuple(record.id for record in discovery_records),
            started_at=CREATED,
            experiment_input_ids=(held_out.id,),
        )
        assert result.status == "stopped", result.stop_reason

        experiment_step = next(
            step for step in result.steps if step.action.kind == "experiment"
        )
        experiment_result = store.get_record(experiment_step.output_ids[1])
        assert experiment_result is not None
        assert experiment_result.payload["observed_positions"] == [3.0]


def test_experiment_input_scope_cannot_overlap_discovery_inputs():
    discovery_records = _records()
    with Store() as store:
        for record in discovery_records:
            store.put_record(record)

        gap = detect_positional_gap(
            store,
            record_ids=tuple(record.id for record in discovery_records),
            position_key="position",
            step=1.0,
            created_at=CREATED,
        )
        assert gap is not None
        store.put_discovery_finding(gap)

        import pytest

        with pytest.raises(
            RuntimeError,
            match="must be disjoint from discovery inputs",
        ):
            run_autonomous_discovery(
                store,
                AdaptiveFixturePlanner(),
                grounded_input_ids=tuple(record.id for record in discovery_records),
                started_at=CREATED,
                experiment_input_ids=(discovery_records[0].id,),
            )
