from episteme.autonomy import DiscoveryAction, DiscoveryContext, run_autonomous_discovery
from episteme.discovery import detect_positional_gap
from episteme.model import Provenance, Record, RecordKind, Store

CREATED = "2026-10-05T00:00:00Z"
PROVENANCE = (Provenance(source_id="autonomy-fixture", captured_at=CREATED, source_location="https://example.org/autonomy", source_version="1"),)


def _records():
    return tuple(
        Record(
            id=f"aaaaaaaa-{index:04d}-4aaa-8aaa-aaaaaaaaaaaa",
            kind=RecordKind.OBSERVATION,
            payload={"position": position},
            provenance=PROVENANCE,
            created_at=CREATED,
        )
        for index, position in enumerate((1.0, 2.0, 4.0), start=1)
    )


class FixturePlanner:
    def __init__(self):
        self.calls = 0

    def choose(self, context: DiscoveryContext) -> DiscoveryAction:
        self.calls += 1
        findings = context.findings
        hypotheses = context.hypotheses
        predictions = context.predictions

        if not hypotheses:
            gap = next(item for item in findings if item["kind"] == "gap")
            return DiscoveryAction(kind="hypothesis", target_ids=(gap["id"],), statement="The missing occupant is at position 3.0.", rationale="The bounded positional gap admits a concrete candidate.")

        if len(hypotheses) == 1:
            gap = next(item for item in findings if item["kind"] == "gap")
            return DiscoveryAction(kind="hypothesis", target_ids=(gap["id"],), statement="The missing occupant is not at position 3.0.", rationale="Preserve a competing explanation before testing.")

        if not predictions:
            return DiscoveryAction(kind="prediction", target_ids=tuple(item["id"] for item in hypotheses), consequence="The measured occupant is at position 3.0.", conditions="Same bounded test conditions.", rationale="The competing hypotheses require a discriminating observation.")

        if len(predictions) == 2:
            return DiscoveryAction(kind="experiment", target_ids=tuple(item["id"] for item in predictions), objective="Distinguish the competing position hypotheses.", proposed_observation="Measure the missing position.", discrimination_basis="The hypotheses imply different outcomes.", conditions="Same bounded test conditions.", rationale="A direct measurement can discriminate the candidates.")

        return DiscoveryAction(kind="stop", rationale="An explicit discriminating experiment now exists; external evidence is required.")


def test_planner_drives_the_loop_without_a_declared_workflow():
    records = _records()
    with Store() as store:
        for record in records:
            store.put_record(record)

        gap = detect_positional_gap(store, record_ids=tuple(record.id for record in records), position_key="position", step=1.0, created_at=CREATED)
        assert gap is not None
        store.put_discovery_finding(gap)

        planner = FixturePlanner()
        result = run_autonomous_discovery(store, planner, grounded_input_ids=tuple(record.id for record in records), started_at=CREATED)

        assert result.status == "stopped"
        assert len(result.steps) == 4
        assert planner.calls == 5
        assert [item.action.kind for item in result.steps] == ["hypothesis", "hypothesis", "prediction", "experiment"]
        assert result.steps[3].output_ids
        assert store.get_experiment_proposal(result.steps[3].output_ids[0]) is not None
