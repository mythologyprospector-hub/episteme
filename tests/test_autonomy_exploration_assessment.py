from episteme import (
    DiscoveryAction,
    DiscoveryContext,
    ExplorationAdmissionRuntime,
    ExplorationAssessmentRuntime,
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
        source_id="autonomy-exploration-fixture",
        captured_at=CREATED,
        source_location="fixture://autonomy-exploration",
        source_version="1",
    ),
)
IDS = (
    "aaaaaaaa-2001-4aaa-8aaa-aaaaaaaaaaaa",
    "aaaaaaaa-2002-4aaa-8aaa-aaaaaaaaaaaa",
)


class ScoutAssessAdmitPlanner:
    def choose(self, context: DiscoveryContext) -> DiscoveryAction:
        if not context.exploration_observations:
            return DiscoveryAction(kind="scout", rationale="Request bounded scouting.")
        observation_id = context.exploration_observations[0]["id"]
        if not context.exploration_observations[0].get("assessed"):
            return DiscoveryAction(
                kind="assess_exploration",
                target_ids=(observation_id,),
                rationale="Request the host-owned assessment policy.",
            )
        return DiscoveryAction(
            kind="admit_exploration",
            target_ids=(observation_id,),
            rationale="Request explicit admission under the host-owned policy.",
        )


def test_autonomous_exploration_can_be_assessed_and_admitted_by_host_policy():
    with Store() as store:
        for record_id, position in zip(IDS, (1.0, 3.0)):
            store.put_record(
                Record(record_id, RecordKind.OBSERVATION, {"position": position}, PROV, CREATED)
            )

        # The fixture planner uses the observation itself as context. Assessment
        # and admission are host-owned policy bindings, not planner decisions.
        class Planner(ScoutAssessAdmitPlanner):
            def choose(self, context):
                if not context.exploration_observations:
                    return DiscoveryAction(kind="scout", rationale="Request bounded scouting.")
                observation_id = context.exploration_observations[0]["id"]
                if not context.feedback and not context.actions_taken[-1].kind == "assess_exploration":
                    return DiscoveryAction(kind="assess_exploration", target_ids=(observation_id,), rationale="Request assessment.")
                return DiscoveryAction(kind="admit_exploration", target_ids=(observation_id,), rationale="Request admission.")

        assessment_runtime = ExplorationAssessmentRuntime(
            allowed_input_ids=IDS,
            accepted=True,
            method="fixture-host-assessment",
            method_version="1",
            rationale="Host policy explicitly permits this generated observation into discovery.",
            provenance=PROV,
        )
        admission_runtime = ExplorationAdmissionRuntime(allowed_input_ids=IDS)
        result = run_autonomous_discovery(
            store,
            Planner(),
            grounded_input_ids=IDS,
            started_at=CREATED,
            max_steps=3,
            exploration_runtime=PositionalExplorationRuntime(
                input_ids=IDS, position_key="position", max_records=2
            ),
            exploration_assessment_runtime=assessment_runtime,
            exploration_admission_runtime=admission_runtime,
        )

        assert result.status == "budget_exhausted"
        assert [step.action.kind for step in result.steps] == [
            "scout",
            "assess_exploration",
            "admit_exploration",
        ]
        observations = list(store.iter_exploration_observations())
        findings = list(store.iter_discovery_findings())
        assessments = list(store.iter_exploration_observation_assessments())
        assert len(observations) == 1
        assert len(assessments) == 1
        assert assessments[0].accepted is True
        assert len(findings) == 1
        assert findings[0].input_ids == IDS
        assert observations[0].id in findings[0].context_ids
        assert assessments[0].id in findings[0].context_ids
        assert store.get_record(observations[0].id) is None


def test_planner_cannot_supply_assessment_acceptance_policy():
    with Store() as store:
        for record_id, position in zip(IDS, (1.0, 3.0)):
            store.put_record(
                Record(record_id, RecordKind.OBSERVATION, {"position": position}, PROV, CREATED)
            )

        class MaliciousPlanner:
            def choose(self, context):
                if not context.exploration_observations:
                    return DiscoveryAction(kind="scout", rationale="Request scouting.")
                return DiscoveryAction(
                    kind="assess_exploration",
                    target_ids=(context.exploration_observations[0]["id"],),
                    accepted=True,
                    method="attacker",
                    rationale="Try to inject assessment policy.",
                )

        runtime = ExplorationAssessmentRuntime(
            allowed_input_ids=IDS,
            accepted=False,
            method="fixture-host-assessment",
            method_version="1",
            rationale="Host policy rejects this fixture for demonstration.",
            provenance=PROV,
        )
        result = run_autonomous_discovery(
            store,
            MaliciousPlanner(),
            grounded_input_ids=IDS,
            started_at=CREATED,
            max_steps=2,
            exploration_runtime=PositionalExplorationRuntime(
                input_ids=IDS, position_key="position", max_records=2
            ),
            exploration_assessment_runtime=runtime,
        )
        assert result.status == "budget_exhausted"
        assessment = list(store.iter_exploration_observation_assessments())[0]
        assert assessment.accepted is False
        assert assessment.method == "fixture-host-assessment"
