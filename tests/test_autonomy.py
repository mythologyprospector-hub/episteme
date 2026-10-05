from episteme.autonomy import DiscoveryAction, DiscoveryContext, PlannerActionError, execute_action, run_autonomous_discovery
from episteme.discovery import detect_positional_gap
from episteme.model import Provenance, Record, RecordKind
from episteme.store import Store

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

    hypotheses = []
    for index, statement in enumerate(("candidate one", "candidate two"), start=1):
        hypothesis = propose_hypothesis(
            statement=statement,
            finding_ids=(f"aaaaaaaa-000{index}-4aaa-8aaa-aaaaaaaaaaaa",),
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
            return DiscoveryAction(kind="prediction", target_ids=tuple(item["id"] for item in hypotheses), consequence="The measured occupant is at position 3.0.", conditions="Same bounded test conditions.", rationale="The competing hypotheses require a discriminating observation.")

        if len(predictions) == 2 and not context.experiments:
            return DiscoveryAction(
                kind="experiment",
                target_ids=tuple(item["id"] for item in predictions),
                objective="Distinguish the competing position hypotheses.",
                proposed_observation="Measure the missing position.",
                discrimination_basis="The hypotheses imply different outcomes.",
                conditions="Same bounded test conditions.",
                execution_spec={
                    "operation": "positional_presence",
                    "position": 3.0,
                    "expected_presence": {
                        predictions[0]["id"]: True,
                        predictions[1]["id"]: False,
                    },
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

        assert result.status == "stopped"
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
        assert "at least two prediction ids" in planner.feedback_seen[0]


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
