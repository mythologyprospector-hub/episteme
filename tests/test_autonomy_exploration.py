"""Proof that autonomy can invoke only a host-owned bounded exploration runtime."""

from episteme import (
    DiscoveryAction,
    DiscoveryContext,
    PositionalExplorationRuntime,
    Provenance,
    Record,
    RecordKind,
    Store,
    run_autonomous_discovery,
)

CREATED = "2026-10-05T00:00:00Z"
PROV = (
    Provenance(
        source_id="autonomy-scout-fixture",
        captured_at=CREATED,
        source_location="https://example.org/autonomy-scout",
        source_version="1",
    ),
)
IDS = (
    "aaaaaaaa-1001-4aaa-8aaa-aaaaaaaaaaaa",
    "aaaaaaaa-1002-4aaa-8aaa-aaaaaaaaaaaa",
    "aaaaaaaa-1003-4aaa-8aaa-aaaaaaaaaaaa",
)


class ScoutThenStopPlanner:
    def __init__(self):
        self.calls = 0

    def choose(self, context: DiscoveryContext) -> DiscoveryAction:
        self.calls += 1
        if not context.exploration_observations:
            return DiscoveryAction(
                kind="scout",
                rationale="Request the host-owned bounded scouting capability.",
            )
        return DiscoveryAction(
            kind="stop",
            rationale="The generated observation now requires explicit downstream assessment.",
        )


def test_autonomous_driver_runs_host_owned_scout_and_exposes_observation():
    with Store() as store:
        for record_id, position in zip(IDS, (1.0, 2.0, 4.0)):
            store.put_record(
                Record(
                    record_id,
                    RecordKind.OBSERVATION,
                    {"position": position},
                    PROV,
                    CREATED,
                )
            )

        planner = ScoutThenStopPlanner()
        runtime = PositionalExplorationRuntime(
            input_ids=IDS,
            position_key="position",
            max_records=3,
        )
        result = run_autonomous_discovery(
            store,
            planner,
            grounded_input_ids=IDS,
            started_at=CREATED,
            max_steps=2,
            exploration_runtime=runtime,
        )

        assert result.status == "stopped"
        assert [step.action.kind for step in result.steps] == ["scout"]
        assert len(result.steps[0].output_ids) == 1
        observation = store.get_exploration_observation(result.steps[0].output_ids[0])
        assert observation is not None
        assert observation.input_ids == IDS
        assert observation.method == "bounded-positional-scout"
        assert list(store.iter_discovery_findings()) == []
        assert store.get_record(observation.id) is None
        assert planner.calls == 2


def test_scout_action_cannot_run_without_host_runtime():
    class ScoutPlanner:
        def choose(self, context):
            return DiscoveryAction(kind="scout", rationale="Request scouting.")

    with Store() as store:
        result = run_autonomous_discovery(
            store,
            ScoutPlanner(),
            grounded_input_ids=IDS,
            started_at=CREATED,
            max_steps=1,
            max_retries_per_step=0,
        )

        assert result.status == "failed"
        assert "host-owned exploration runtime" in result.stop_reason
        assert list(store.iter_exploration_observations()) == []
