"""Phase 13 proof of durable workflow execution history."""

import sqlite3

from episteme import Provenance, Record, RecordKind, Store
from episteme.orchestration import (
    WorkflowDefinition,
    WorkflowStep,
    WorkflowStepResult,
    WorkflowExecution,
    run_workflow,
)


CREATED = "2026-09-19T00:00:00Z"
PROVENANCE = (
    Provenance(
        source_id="phase13-fixture",
        captured_at=CREATED,
        source_location="https://example.org/phase13",
        source_version="1",
    ),
)


def _workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        id="phase13-workflow",
        name="Durable history fixture",
        method="phase13-fixture-workflow",
        method_version="1",
        input_ids=("phase13-input",),
        steps=(
            WorkflowStep(
                "step-one", "first", "phase13-first", "1", ("phase13-input",)
            ),
            WorkflowStep("step-two", "second", "phase13-second", "2"),
        ),
        assumptions=("Fixture assumption.",),
    )


def _records() -> tuple[Record, Record]:
    return (
        Record(
            id="phase13-input",
            kind=RecordKind.OBSERVATION,
            payload={"value": 1},
            provenance=PROVENANCE,
            created_at=CREATED,
        ),
        Record(
            id="phase13-output",
            kind=RecordKind.RESULT,
            payload={"value": 2},
            provenance=PROVENANCE,
            created_at=CREATED,
        ),
    )


def test_workflow_definition_persists_and_recovers_without_semantic_change(tmp_path):
    path = tmp_path / "phase13.sqlite"
    workflow = _workflow()

    with Store(path) as store:
        store.put_workflow_definition(workflow)

    with Store(path) as store:
        recovered = store.get_workflow_definition(workflow.id)

    assert recovered == workflow
    assert recovered.lineage_dict() == workflow.lineage_dict()


def test_workflow_execution_survives_process_boundary_with_lineage_intact(tmp_path):
    path = tmp_path / "phase13.sqlite"
    workflow = _workflow()
    input_record, output_record = _records()

    with Store(path) as store:
        store.put_record(input_record)
        store.put_record(output_record)
        store.put_workflow_definition(workflow)

        def first(step, input_ids):
            assert input_ids == ("phase13-input",)
            return ("phase13-output",)

        def second(step, input_ids):
            assert input_ids == ("phase13-output",)
            return ("phase13-input",)

        execution = run_workflow(
            workflow,
            {"first": first, "second": second},
            started_at=CREATED,
        )
        store.put_workflow_execution(execution)

    with Store(path) as store:
        recovered = store.get_workflow_execution(execution.id)

    assert recovered == execution
    assert recovered.lineage_dict() == execution.lineage_dict()
    assert recovered.step_results[0].method_version == "1"
    assert recovered.step_results[1].method_version == "2"
    assert recovered.step_results[1].input_ids == ("phase13-output",)


def test_failed_execution_is_persisted_without_erasing_prior_steps(tmp_path):
    path = tmp_path / "phase13.sqlite"
    workflow = WorkflowDefinition(
        id="phase13-failure",
        name="Durable failure fixture",
        method="phase13-failure-workflow",
        method_version="1",
        input_ids=("phase13-input",),
        steps=(
            WorkflowStep("step-one", "first", "phase13-first", "1", ("phase13-input",)),
            WorkflowStep("step-two", "missing", "phase13-missing", "7"),
        ),
    )
    input_record, output_record = _records()

    with Store(path) as store:
        store.put_record(input_record)
        store.put_record(output_record)
        store.put_workflow_definition(workflow)

        def first(step, input_ids):
            return ("phase13-output",)

        execution = run_workflow(
            workflow, {"first": first}, started_at=CREATED
        )
        store.put_workflow_execution(execution)

    with Store(path) as store:
        recovered = store.get_workflow_execution(execution.id)

    assert recovered.status == "failed"
    assert recovered.step_results[0].status == "completed"
    assert recovered.step_results[0].output_ids == ("phase13-output",)
    assert recovered.step_results[1].status == "failed"
    assert recovered.step_results[1].input_ids == ("phase13-output",)
    assert recovered.step_results[1].method_version == "7"
    assert "no executor declared" in recovered.step_results[1].error


def test_workflow_history_is_immutable(tmp_path):
    path = tmp_path / "phase13.sqlite"
    workflow = _workflow()
    input_record, output_record = _records()

    with Store(path) as store:
        store.put_record(input_record)
        store.put_record(output_record)
        store.put_workflow_definition(workflow)
        execution = run_workflow(
            workflow,
            {"first": lambda step, ids: ("phase13-output",),
             "second": lambda step, ids: ("phase13-input",)},
            started_at=CREATED,
        )
        store.put_workflow_execution(execution)

        try:
            store.put_workflow_definition(workflow)
            raise AssertionError("duplicate workflow definition was accepted")
        except sqlite3.IntegrityError:
            pass

        try:
            store.put_workflow_execution(execution)
            raise AssertionError("duplicate workflow execution was accepted")
        except sqlite3.IntegrityError:
            pass

        assert store.get_workflow_definition(workflow.id) == workflow
        assert store.get_workflow_execution(execution.id) == execution


def test_execution_history_does_not_change_grounded_or_generated_artifacts(tmp_path):
    path = tmp_path / "phase13.sqlite"
    workflow = _workflow()
    input_record, output_record = _records()

    with Store(path) as store:
        store.put_record(input_record)
        store.put_record(output_record)
        store.put_workflow_definition(workflow)
        execution = WorkflowExecution(
            id="phase13-execution",
            workflow_id=workflow.id,
            workflow_method=workflow.method,
            workflow_method_version=workflow.method_version,
            status="completed",
            step_results=(
                WorkflowStepResult(
                    step_id="step-one",
                    method="phase13-first",
                    method_version="1",
                    status="completed",
                    input_ids=("phase13-input",),
                    output_ids=("phase13-output",),
                ),
            ),
            started_at=CREATED,
            completed_at=CREATED,
        )
        store.put_workflow_execution(execution)

        assert store.get_record("phase13-input").kind is RecordKind.OBSERVATION
        assert store.get_record("phase13-output").kind is RecordKind.RESULT
        assert store.get_workflow_execution(execution.id) == execution
