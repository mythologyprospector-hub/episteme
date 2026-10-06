from episteme.autonomy import DiscoveryAction, DiscoveryContext, PlannerActionError, execute_action, run_autonomous_discovery
from episteme.discovery import detect_positional_gap
from episteme.model import Provenance, Record, RecordKind
from episteme.store import Store
from episteme.evidence_request import EvidenceRequestRejected

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


def _grounded_test_predictions(store):
    from episteme.proposals import propose_discriminating_prediction, propose_hypothesis

    records = _records()
    for record in records:
        store.put_record(record)
    gap = detect_positional_gap(
        store,
        record_ids=tuple(record.id for record in records),
        position_key="position",
        step=1.0,
        created_at=CREATED,
    )
    assert gap is not None
    store.put_discovery_finding(gap)

    hypotheses = []
    for statement in ("candidate one", "candidate two"):
        hypothesis = propose_hypothesis(
            statement=statement,
            finding_ids=(gap.id,),
            input_ids=tuple(record.id for record in records),
            method="fixture",
            method_version="1",
            rationale="fixture",
            created_at=CREATED,
        )
        store.put_hypothesis(hypothesis)
        hypotheses.append(hypothesis)

    predictions = []
    for hypothesis in hypotheses:
        prediction = propose_discriminating_prediction(
            store,
            candidate_id=hypothesis.id,
            competing_candidate_ids=tuple(item.id for item in hypotheses),
            consequence="test",
            conditions="test",
            method="fixture",
            method_version="1",
            rationale="fixture",
            created_at=CREATED,
        )
        store.put_prediction(prediction)
        predictions.append(prediction)
    return tuple(predictions)


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
            return DiscoveryAction(kind="prediction", target_ids=tuple(item["id"] for item in hypotheses), consequence="The measured occupant is at position 3.0.", conditions="Same bounded test conditions.", expected_presences={item["id"]: (index == 0) for index, item in enumerate(hypotheses)}, rationale="The competing hypotheses require a discriminating observation.")

        if len(predictions) == 2 and not context.experiments:
            return DiscoveryAction(
                kind="experiment",
                target_ids=tuple(item["id"] for item in predictions),
                objective="Distinguish the competing position hypotheses.",
                proposed_observation="Measure the missing position.",
                discrimination_basis="The hypotheses imply different outcomes.",
                conditions="Same bounded test conditions.",
                expected_presences={
                    predictions[0]["id"]: True,
                    predictions[1]["id"]: False,
                },
                execution_spec={
                    "operation": "positional_presence",
                    "position": 3.0,
                },
                rationale="A direct measurement can discriminate the candidates.",
            )

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

        assert result.status == "stopped", result.stop_reason
        assert len(result.steps) == 4
        assert planner.calls == 5
        assert [item.action.kind for item in result.steps] == ["hypothesis", "hypothesis", "prediction", "experiment"]
        assert result.steps[3].output_ids
        assert store.get_experiment_proposal(result.steps[3].output_ids[0]) is not None

def test_invalid_prediction_action_does_not_persist_partial_outputs():
    records = _records()
    with Store() as store:
        for record in records:
            store.put_record(record)

        gap = detect_positional_gap(
            store,
            record_ids=tuple(record.id for record in records),
            position_key="position",
            step=1.0,
            created_at=CREATED,
        )
        assert gap is not None
        store.put_discovery_finding(gap)

        from episteme.proposals import propose_hypothesis

        hypotheses = []
        for statement in ("The missing occupant is at position 3.0.", "The missing occupant is absent."):
            hypothesis = propose_hypothesis(
                statement=statement,
                finding_ids=(gap.id,),
                input_ids=tuple(record.id for record in records),
                method="fixture",
                method_version="1",
                rationale="fixture",
                created_at=CREATED,
            )
            store.put_hypothesis(hypothesis)
            hypotheses.append(hypothesis)

        action = DiscoveryAction(
            kind="prediction",
            target_ids=(hypotheses[0].id, "missing-hypothesis"),
            consequence="The measured occupant is present.",
            conditions="Same bounded test conditions.",
            rationale="Intentionally invalid second target.",
        )

        try:
            execute_action(store, action, created_at=CREATED)
        except PlannerActionError as exc:
            assert "missing candidate" in str(exc)
        else:
            raise AssertionError("invalid prediction action was accepted")

        assert tuple(store.iter_predictions()) == ()



def test_executable_spec_cannot_select_unregistered_operation():
    action = DiscoveryAction(
        kind="experiment",
        target_ids=("prediction-a", "prediction-b"),
        objective="test",
        proposed_observation="test",
        discrimination_basis="test",
        conditions="test",
        execution_spec={
            "operation": "run_python",
            "position": 3.0,
            "expected_presence": {},
        },
        rationale="Reject an operation outside the registered vocabulary.",
    )
    try:
        execute_action(Store(), action, created_at=CREATED)
    except PlannerActionError as exc:
        assert "unsupported executable experiment operation" in str(exc)
    else:
        raise AssertionError("unregistered executable operation was accepted")




def test_executable_spec_must_match_prediction_ids():
    action = DiscoveryAction(
        kind="experiment",
        target_ids=("prediction-a", "prediction-b"),
        objective="test",
        proposed_observation="test",
        discrimination_basis="test",
        conditions="test",
        execution_spec={
            "operation": "positional_presence",
            "position": 3.0,
            "expected_presence": {"prediction-a": True},
        },
        rationale="Reject incomplete executable expectations.",
    )
    with Store() as store:
        try:
            execute_action(store, action, created_at=CREATED)
        except PlannerActionError as exc:
            assert "expected_presence must exactly match" in str(exc)
        else:
            raise AssertionError("incomplete executable expectations were accepted")


def test_executable_spec_rejects_unregistered_control_fields():
    action = DiscoveryAction(
        kind="experiment",
        target_ids=("prediction-a", "prediction-b"),
        objective="test",
        proposed_observation="test",
        discrimination_basis="test",
        conditions="test",
        execution_spec={
            "operation": "positional_presence",
            "position": 3.0,
            "expected_presence": {
                "prediction-a": True,
                "prediction-b": False,
            },
            "executor": "arbitrary.callable",
        },
        rationale="Reject planner-supplied executable control data.",
    )
    with Store() as store:
        try:
            execute_action(store, action, created_at=CREATED)
        except PlannerActionError as exc:
            assert "invalid execution_spec" in str(exc)
        else:
            raise AssertionError("planner-supplied executable control field was accepted")


class AdaptiveFixturePlanner(FixturePlanner):
    def __init__(self):
        super().__init__()
        self.state_observed = False

    def choose(self, context: DiscoveryContext) -> DiscoveryAction:
        action = super().choose(context)
        if context.evaluations and context.consequences:
            outcomes = {item["outcome"] for item in context.evaluations}
            consequence_kinds = {item["consequence"] for item in context.consequences}
            if outcomes == {"consistent", "inconsistent"} and consequence_kinds == {"supports", "contradicts"}:
                self.state_observed = True
                return DiscoveryAction(
                    kind="stop",
                    rationale="The changing knowledge state now contains one supported and one contradicted prediction; further action requires new grounded evidence.",
                )
        return action


def test_experiment_is_executed_evaluated_and_changes_planner_knowledge_state():
    records = _records()
    with Store() as store:
        for record in records:
            store.put_record(record)

        gap = detect_positional_gap(
            store,
            record_ids=tuple(record.id for record in records),
            position_key="position",
            step=1.0,
            created_at=CREATED,
        )
        assert gap is not None
        store.put_discovery_finding(gap)

        planner = AdaptiveFixturePlanner()
        result = run_autonomous_discovery(
            store,
            planner,
            grounded_input_ids=tuple(record.id for record in records),
            started_at=CREATED,
       )

        assert result.status == "stopped"
        assert len(result.steps) == 4
        assert planner.calls == 5
        assert len(tuple(store.iter_prediction_evaluations())) == 2
        assert len(tuple(store.iter_knowledge_state_consequences())) == 2
        assert len(result.steps[3].output_ids) == 1 + 1 + 2 + 2
        assert planner.state_observed is True
        assert result.stop_reason is not None

class RecoveringPlanner:
    def __init__(self):
        self.calls = 0
        self.feedback_seen = ()

    def choose(self, context: DiscoveryContext) -> DiscoveryAction:
        self.calls += 1
        self.feedback_seen = context.feedback
        if self.calls == 1:
            return DiscoveryAction(
                kind="experiment",
                target_ids=("not-a-prediction",),
                objective="Invalid first attempt.",
                proposed_observation="Invalid first attempt.",
                discrimination_basis="Invalid first attempt.",
                conditions="Invalid first attempt.",
                execution_spec={
                    "operation": "positional_presence",
                    "position": 3.0,
                    "expected_presence": {},
                },
                rationale="This intentionally violates the experiment target contract.",
            )
        gap = next(item for item in context.findings if item["kind"] == "gap")
        return DiscoveryAction(
            kind="hypothesis",
            target_ids=(gap["id"],),
            statement="The missing occupant is at position 3.0.",
            rationale="The retry feedback identified an invalid experiment target, so propose a valid hypothesis.",
        )


def test_invalid_action_is_fed_back_to_planner_for_bounded_retry():
    records = _records()
    with Store() as store:
        for record in records:
            store.put_record(record)

        gap = detect_positional_gap(
            store,
            record_ids=tuple(record.id for record in records),
            position_key="position",
            step=1.0,
            created_at=CREATED,
        )
        assert gap is not None
        store.put_discovery_finding(gap)

        planner = RecoveringPlanner()
        result = run_autonomous_discovery(
            store,
            planner,
            grounded_input_ids=tuple(record.id for record in records),
            started_at=CREATED,
            max_steps=1,
            max_retries_per_step=1,
        )

        assert result.status == "budget_exhausted"
        assert len(result.steps) == 1
        assert result.steps[0].action.kind == "hypothesis"
        assert planner.calls == 2
        assert planner.feedback_seen
        assert "initial hypothesis before predictions" in planner.feedback_seen[0]


def test_execution_spec_rejects_invalid_parameter_shapes():
    cases = (
        {
            "operation": "positional_presence",
            "position": True,
            "expected_presence": {},
        },
        {
            "operation": "positional_presence",
            "position": float("nan"),
            "expected_presence": {},
        },
        {
            "operation": "positional_presence",
            "position": 3.0,
            "position_key": "",
            "expected_presence": {},
        },
        {
            "operation": "positional_presence",
            "position": 3.0,
            "expected_presence": [],
        },
        {
            "operation": "positional_presence",
            "position": 3.0,
            "expected_presence": {"prediction-a": "true"},
        },
        {
            "operation": "positional_presence",
            "position": 3.0,
            "expected_presence": {1: True},
        },
    )

    for spec in cases:
        action = DiscoveryAction(
            kind="experiment",
            target_ids=("prediction-a", "prediction-b"),
            objective="test",
            proposed_observation="test",
            discrimination_basis="test",
            conditions="test",
            execution_spec=spec,
            rationale="Reject invalid executable parameter shapes.",
        )
        with Store() as store:
            try:
                execute_action(store, action, created_at=CREATED)
            except PlannerActionError as exc:
                assert "invalid execution_spec" in str(exc)
            else:
                raise AssertionError(f"invalid execution spec was accepted: {spec!r}")


def test_execution_spec_rejects_extra_runtime_controls():
    action = DiscoveryAction(
        kind="experiment",
        target_ids=("prediction-a", "prediction-b"),
        objective="test",
        proposed_observation="test",
        discrimination_basis="test",
        conditions="test",
        execution_spec={
            "operation": "positional_presence",
            "position": 3.0,
            "expected_presence": {
                "prediction-a": True,
                "prediction-b": False,
            },
            "command": "echo should-not-run",
            "url": "https://example.invalid",
            "evaluator": "arbitrary.evaluator",
        },
        rationale="Reject fields that could redirect runtime behavior.",
    )
    with Store() as store:
        try:
            execute_action(store, action, created_at=CREATED)
        except PlannerActionError as exc:
            assert "invalid execution_spec" in str(exc)
        else:
            raise AssertionError("runtime-control fields were accepted")



def test_grounded_executor_rejects_missing_input_record():
    from episteme.executor import PositionalObservationExecutor
    from episteme.model import ExperimentProposal

    missing_id = "bbbbbbbb-0001-4aaa-8aaa-bbbbbbbbbbbb"
    with Store() as store:
        predictions = _grounded_test_predictions(store)
        proposal = ExperimentProposal(
            id="cccccccc-0001-4aaa-8aaa-cccccccccccc",
            prediction_ids=tuple(item.id for item in predictions),
            objective="test",
            proposed_observation="test",
            discrimination_basis="test",
            conditions="test",
            assumptions=(),
            method="fixture",
            method_version="1",
            rationale="fixture",
            created_at=CREATED,
            execution_spec={
                "operation": "positional_presence",
                "position": 3.0,
                "expected_presence": {predictions[0].id: True, predictions[1].id: False},
            },
        )
        store.put_experiment_proposal(proposal)
        try:
            PositionalObservationExecutor().execute(store, proposal, input_ids=(missing_id,), created_at=CREATED)
        except ValueError as exc:
            assert "references missing record" in str(exc)
        else:
            raise AssertionError("missing grounded input was accepted")


def test_grounded_executor_rejects_non_observation_input():
    from episteme.executor import PositionalObservationExecutor
    from episteme.model import ExperimentProposal

    result_id = "dddddddd-0001-4aaa-8aaa-dddddddddddd"
    result_record = Record(
        id=result_id,
        kind=RecordKind.RESULT,
        payload={"position": 3.0},
        provenance=PROVENANCE,
        created_at=CREATED,
    )
    with Store() as store:
        predictions = _grounded_test_predictions(store)
        proposal = ExperimentProposal(
            id="eeeeeeee-0001-4aaa-8aaa-eeeeeeeeeeee",
            prediction_ids=tuple(item.id for item in predictions),
            objective="test",
            proposed_observation="test",
            discrimination_basis="test",
            conditions="test",
            assumptions=(),
            method="fixture",
            method_version="1",
            rationale="fixture",
            created_at=CREATED,
            execution_spec={
                "operation": "positional_presence",
                "position": 3.0,
                "expected_presence": {predictions[0].id: True, predictions[1].id: False},
            },
        )
        store.put_record(result_record)
        store.put_experiment_proposal(proposal)
        try:
            PositionalObservationExecutor().execute(store, proposal, input_ids=(result_id,), created_at=CREATED)
        except ValueError as exc:
            assert "requires observation records" in str(exc)
        else:
            raise AssertionError("non-observation grounded input was accepted")


class PrematurePredictionPlanner:
    def choose(self, context: DiscoveryContext) -> DiscoveryAction:
        hypotheses = context.hypotheses
        target_ids = tuple(item["id"] for item in hypotheses)
        if len(target_ids) >= 2:
            return DiscoveryAction(
                kind="prediction",
                target_ids=target_ids,
                consequence="The measured occupant is present.",
                conditions="Same bounded test conditions.",
                rationale="Test the competing hypotheses.",
            )
        return DiscoveryAction(
            kind="prediction",
            target_ids=target_ids,
            consequence="The measured occupant is present.",
            conditions="Same bounded test conditions.",
            rationale="Intentionally attempt prediction before the host state permits it.",
        )


def test_host_state_machine_rejects_prediction_before_competing_hypotheses():
    records = _records()
    with Store() as store:
        for record in records:
            store.put_record(record)

        gap = detect_positional_gap(
            store,
            record_ids=tuple(record.id for record in records),
            position_key="position",
            step=1.0,
            created_at=CREATED,
        )
        assert gap is not None
        store.put_discovery_finding(gap)

        result = run_autonomous_discovery(
            store,
            PrematurePredictionPlanner(),
            grounded_input_ids=tuple(record.id for record in records),
            started_at=CREATED,
            max_steps=1,
            max_retries_per_step=0,
        )

        assert result.status == "failed"
        assert result.stop_reason is not None
        assert "GAP or TENSION" in result.stop_reason
        assert tuple(store.iter_predictions()) == ()


class PrematureStopPlanner:
    def choose(self, context: DiscoveryContext) -> DiscoveryAction:
        return DiscoveryAction(
            kind="stop",
            rationale="Intentionally attempt termination before an experiment.",
        )


def test_host_state_machine_rejects_stop_before_experiment():
    records = _records()
    with Store() as store:
        for record in records:
            store.put_record(record)

        gap = detect_positional_gap(
            store,
            record_ids=tuple(record.id for record in records),
            position_key="position",
            step=1.0,
            created_at=CREATED,
        )
        assert gap is not None
        store.put_discovery_finding(gap)

        result = run_autonomous_discovery(
            store,
            PrematureStopPlanner(),
            grounded_input_ids=tuple(record.id for record in records),
            started_at=CREATED,
            max_steps=1,
            max_retries_per_step=0,
        )

        assert result.status == "failed"
        assert result.stop_reason is not None
        assert "before a bounded experiment" in result.stop_reason


class EvidenceRequestPlanner(AdaptiveFixturePlanner):
    def choose(self, context: DiscoveryContext) -> DiscoveryAction:
        if context.evaluations and not any(
            action.kind == "request_evidence" for action in context.actions_taken
        ):
            return DiscoveryAction(
                kind="request_evidence",
                target_ids=(context.predictions[0]["id"],),
                evidence_capability="crossref_works",
                evidence_parameters={"rows": 1, "query.title": "bounded discovery"},
                requested_representation="application/json",
                rationale="The evaluated experiment leaves an external evidence question that should be answered through a host-approved capability.",
            )
        if any(action.kind == "request_evidence" for action in context.actions_taken):
            return DiscoveryAction(
                kind="stop",
                rationale="The bounded evidence request has completed; stop without treating the capture as grounded truth.",
            )
        return super().choose(context)


class CrossrefEvidenceRuntime:
    def request_evidence(self, store, request, *, created_at):
        from episteme.acquisition import AcquisitionResponse
        from episteme.capture import CaptureOutcome
        from episteme.evidence_request import execute_evidence_request

        return execute_evidence_request(
            request,
            store,
            provider=lambda _request: AcquisitionResponse(
                status=200,
                media_type="application/json",
                source_version="fixture-crossref-v1",
                content=b'{"message":{"items":[]}}',
                outcome=CaptureOutcome.COMPLETE,
            ),
            captured_at=created_at,
            capture_id="capture-autonomous-evidence",
        )



    
class RejectedEvidenceRuntime:
    def request_evidence(self, store, request, *, created_at):
        raise EvidenceRequestRejected("fixture host admission policy denied the request")



class FailedEvidenceRuntime:
    def request_evidence(self, store, request, *, created_at):
        from episteme.acquisition import AcquisitionResponse
        from episteme.capture import CaptureOutcome
        from episteme.evidence_request import execute_evidence_request
        return execute_evidence_request(
            request, store,
            provider=lambda _request: AcquisitionResponse(
                status=None, media_type=None, source_version="fixture-crossref-v1",
                content=None, outcome=CaptureOutcome.FAILED, error="fixture acquisition failed",
            ),
            captured_at=created_at, capture_id="capture-autonomous-evidence-failed",
        )


class PartialEvidenceRuntime:
    def request_evidence(self, store, request, *, created_at):
        from episteme.acquisition import AcquisitionResponse
        from episteme.capture import CaptureOutcome
        from episteme.evidence_request import execute_evidence_request
        return execute_evidence_request(
            request, store,
            provider=lambda _request: AcquisitionResponse(
                status=206, media_type="application/json", source_version="fixture-crossref-v1",
                content=b'{"message":{"items":[]}}', outcome=CaptureOutcome.PARTIAL,
            ),
            captured_at=created_at, capture_id="capture-autonomous-evidence-partial",
        )




class MalformedOutcomeEvidenceRuntime:
    def request_evidence(self, store, request, *, created_at):
        return type("MalformedCapture", (), {"id": "malformed-capture", "outcome": "complete"})()


class UnsupportedMediaEvidenceRuntime:
    def request_evidence(self, store, request, *, created_at):
        from episteme.acquisition import AcquisitionResponse
        from episteme.capture import CaptureOutcome
        from episteme.evidence_request import execute_evidence_request
        return execute_evidence_request(
            request, store,
            provider=lambda _request: AcquisitionResponse(
                status=200, media_type="text/html", source_version="fixture-crossref-v1",
                content=b"<html>not the registered representation</html>",
                outcome=CaptureOutcome.COMPLETE,
            ),
            captured_at=created_at, capture_id="capture-autonomous-evidence-media-mismatch",
        )


def _run_autonomous_evidence_fixture(tmp_path, runtime):
    records = _records()
    db_path = tmp_path / "phase28-autonomous.sqlite"
    with Store(db_path, capture_root=tmp_path / "captures") as store:
        for record in records:
            store.put_record(record)
        gap = detect_positional_gap(
            store, record_ids=tuple(record.id for record in records),
            position_key="position", step=1.0, created_at=CREATED,
        )
        assert gap is not None
        store.put_discovery_finding(gap)
        result = run_autonomous_discovery(
            store, EvidenceRequestPlanner(),
            grounded_input_ids=tuple(record.id for record in records),
            started_at=CREATED, evidence_request_runtime=runtime, max_steps=6,
        )
        return result, db_path


def test_autonomous_host_rejection_creates_no_capture(tmp_path):
    result, db_path = _run_autonomous_evidence_fixture(
        tmp_path, RejectedEvidenceRuntime()
    )
    assert result.status == "failed", result.stop_reason
    assert "rejected by host policy" in result.stop_reason
    assert tuple(step.action.kind for step in result.steps) == ("hypothesis", "hypothesis", "prediction", "experiment")
    with Store(db_path, capture_root=tmp_path / "captures") as store:
        assert tuple(store.iter_captured_representations()) == ()

def test_autonomous_evidence_failure_is_not_reported_as_success(tmp_path):
    result, db_path = _run_autonomous_evidence_fixture(tmp_path, FailedEvidenceRuntime())
    assert result.status == "failed", result.stop_reason
    assert "failed" in result.stop_reason
    capture_id = result.steps[-1].output_ids[0]
    with Store(db_path, capture_root=tmp_path / "captures") as store:
        capture = store.get_captured_representation(capture_id)
        assert capture is not None
        assert capture.outcome.value == "failed"
        assert store.get_record(capture_id) is None


def test_autonomous_partial_evidence_is_not_reported_as_complete(tmp_path):
    result, db_path = _run_autonomous_evidence_fixture(tmp_path, PartialEvidenceRuntime())
    assert result.status == "failed", result.stop_reason
    assert "partial capture" in result.stop_reason
    capture_id = result.steps[-1].output_ids[0]
    with Store(db_path, capture_root=tmp_path / "captures") as store:
        capture = store.get_captured_representation(capture_id)
        assert capture is not None
        assert capture.outcome.value == "partial"
        assert store.get_record(capture_id) is None


def test_autonomous_malformed_evidence_outcome_is_rejected(tmp_path):
    import pytest

    with pytest.raises(
        RuntimeError,
        match="invalid capture outcome",
    ):
        _run_autonomous_evidence_fixture(
            tmp_path, MalformedOutcomeEvidenceRuntime()
        )


def test_autonomous_evidence_media_mismatch_is_not_reported_as_success(tmp_path):
    result, db_path = _run_autonomous_evidence_fixture(
        tmp_path, UnsupportedMediaEvidenceRuntime()
    )
    assert result.status == "failed", result.stop_reason
    capture_id = result.steps[-1].output_ids[0]
    with Store(db_path, capture_root=tmp_path / "captures") as store:
        capture = store.get_captured_representation(capture_id)
        assert capture is not None
        assert capture.outcome.value == "failed"
        assert "media type" in (capture.error or "")
        assert store.get_record(capture_id) is None

def test_autonomous_discovery_can_request_evidence_only_through_host_runtime(tmp_path):
    records = _records()
    with Store(capture_root=tmp_path / "captures") as store:
        for record in records:
            store.put_record(record)

        gap = detect_positional_gap(
            store,
            record_ids=tuple(record.id for record in records),
            position_key="position",
            step=1.0,
            created_at=CREATED,
        )
        assert gap is not None
        store.put_discovery_finding(gap)

        planner = EvidenceRequestPlanner()
        result = run_autonomous_discovery(
            store,
            planner,
            grounded_input_ids=tuple(record.id for record in records),
            started_at=CREATED,
            evidence_request_runtime=CrossrefEvidenceRuntime(),
            max_steps=6,
        )

        assert result.status == "stopped", result.stop_reason
        assert [step.action.kind for step in result.steps] == [
            "hypothesis",
            "hypothesis",
            "prediction",
            "experiment",
            "request_evidence",
        ]
        capture_id = result.steps[-1].output_ids[0]
        capture = store.get_captured_representation(capture_id)
        assert capture is not None
        assert capture.outcome.value == "complete"
        assert store.read_captured_content(capture_id) == b'{"message":{"items":[]}}'
        assert store.get_record(capture_id) is None
