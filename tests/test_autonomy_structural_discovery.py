from episteme import (
    DiscoveryAction,
    DiscoveryContext,
    PositionalExplorationRuntime,
    PositionalGapDiscoveryRuntime,
    Provenance,
    Record,
    RecordKind,
    Store,
    run_autonomous_discovery,
)

CREATED = "2026-10-06T00:00:00Z"
PROV = (
    Provenance(
        source_id="structural-autonomy-fixture",
        captured_at=CREATED,
        source_location="fixture://structural-autonomy",
        source_version="1",
    ),
)
IDS = (
    "bbbbbbbb-3001-4aaa-8aaa-bbbbbbbbbbbb",
    "bbbbbbbb-3002-4aaa-8aaa-bbbbbbbbbbbb",
    "bbbbbbbb-3003-4aaa-8aaa-bbbbbbbbbbbb",
)


class ScoutDiscoverPlanner:
    def choose(self, context: DiscoveryContext) -> DiscoveryAction:
        if not context.exploration_observations:
            return DiscoveryAction(kind="scout", rationale="Start bounded exploration.")
        if not context.findings:
            return DiscoveryAction(kind="discover_gap", rationale="Request the host-owned bounded structural discovery pass.")
        return DiscoveryAction(kind="stop", rationale="The bounded structural discovery result is now available.")


def test_autonomous_exploration_can_reach_host_owned_structural_discovery():
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

        result = run_autonomous_discovery(
            store,
            ScoutDiscoverPlanner(),
            grounded_input_ids=IDS,
            started_at=CREATED,
            max_steps=4,
            exploration_runtime=PositionalExplorationRuntime(
                input_ids=IDS,
                position_key="position",
                max_records=3,
            ),
            structural_discovery_runtime=PositionalGapDiscoveryRuntime(
                input_ids=IDS,
                position_key="position",
                step=1.0,
            ),
        )

        assert [step.action.kind for step in result.steps] == ["scout", "discover_gap"]
        findings = tuple(store.iter_discovery_findings())
        assert len(findings) == 1
        assert findings[0].kind.value == "gap"
        assert findings[0].input_ids == IDS
        observations = tuple(store.iter_exploration_observations())
        assert len(observations) == 1
        assert store.get_record(observations[0].id) is None


def test_planner_cannot_execute_structural_discovery_without_host_runtime():
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

        result = run_autonomous_discovery(
            store,
            ScoutDiscoverPlanner(),
            grounded_input_ids=IDS,
            started_at=CREATED,
            max_steps=2,
            exploration_runtime=PositionalExplorationRuntime(
                input_ids=IDS,
                position_key="position",
                max_records=3,
            ),
            max_retries_per_step=0,
        )

        assert result.status == "failed"
        assert "structural discovery is unavailable" in (result.stop_reason or "")


class GapHypothesisPlanner:
    def choose(self, context: DiscoveryContext) -> DiscoveryAction:
        if not context.exploration_observations:
            return DiscoveryAction(kind="scout", rationale="Start bounded exploration.")
        if not context.findings:
            return DiscoveryAction(kind="discover_gap", rationale="Find the bounded structural gap.")
        if not context.hypotheses:
            return DiscoveryAction(
                kind="hypothesis",
                target_ids=(context.findings[-1]["id"],),
                statement="A missing position is structurally meaningful.",
                rationale="Complete the established gap with a generated candidate.",
            )
        return DiscoveryAction(kind="stop", rationale="The generated hypothesis is now available.")


def test_gap_hypothesis_uses_host_owned_structural_completion():
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

        result = run_autonomous_discovery(
            store,
            GapHypothesisPlanner(),
            grounded_input_ids=IDS,
            started_at=CREATED,
            max_steps=6,
            exploration_runtime=PositionalExplorationRuntime(
                input_ids=IDS,
                position_key="position",
                max_records=3,
            ),
            structural_discovery_runtime=PositionalGapDiscoveryRuntime(
                input_ids=IDS,
                position_key="position",
                step=1.0,
            ),
        )

        assert [step.action.kind for step in result.steps] == [
            "scout",
            "discover_gap",
            "hypothesis",
        ]
        findings = tuple(store.iter_discovery_findings())
        assert len(findings) == 1
        hypotheses = tuple(store.iter_hypotheses())
        assert len(hypotheses) == 1
        hypothesis = hypotheses[0]
        assert hypothesis.finding_ids == (findings[0].id,)
        assert hypothesis.input_ids == IDS
        assert hypothesis.method == "planner-driven-structural-gap-completion"
        assert hypothesis.method_version == "1"
        assert store.get_discovery_finding(findings[0].id) == findings[0]
