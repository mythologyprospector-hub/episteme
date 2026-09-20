"""Phase 14 proof of public execution traceability."""

import json
from threading import Thread
from urllib.request import urlopen

from episteme import (
    Provenance,
    Record,
    RecordKind,
    Store,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowStep,
    WorkflowStepResult,
    get_workflow_definition,
    get_workflow_execution,
    list_workflow_definitions,
    list_workflow_executions,
    workflow_execution_lineage,
)
from episteme.http_api import create_http_server


CREATED = "2026-09-20T00:00:00Z"
INPUT_ID = "11111111-1111-4111-8111-111111111111"
OUTPUT_ID = "22222222-2222-4222-8222-222222222222"
WORKFLOW_ID = "33333333-3333-4333-8333-333333333331"
EXECUTION_ID = "33333333-3333-4333-8333-333333333332"
PROVENANCE = (
    Provenance(
        source_id="phase14-fixture",
        captured_at=CREATED,
        source_location="https://example.org/phase14",
        source_version="1",
    ),
)


def _workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        id=WORKFLOW_ID,
        name="Public traceability fixture",
        method="phase14-fixture-workflow",
        method_version="1",
        input_ids=(INPUT_ID,),
        steps=(
            WorkflowStep("step-one", "first", "phase14-first", "1", (INPUT_ID,)),
            WorkflowStep("step-two", "second", "phase14-second", "2"),
        ),
    )


def _execution(workflow: WorkflowDefinition) -> WorkflowExecution:
    return WorkflowExecution(
        id=EXECUTION_ID,
        workflow_id=workflow.id,
        workflow_method=workflow.method,
        workflow_method_version=workflow.method_version,
        status="completed",
        step_results=(
            WorkflowStepResult(
                step_id="step-one",
                method="phase14-first",
                method_version="1",
                status="completed",
                input_ids=(INPUT_ID,),
                output_ids=(OUTPUT_ID,),
            ),
            WorkflowStepResult(
                step_id="step-two",
                method="phase14-second",
                method_version="2",
                status="completed",
                input_ids=(OUTPUT_ID,),
                output_ids=(INPUT_ID,),
            ),
        ),
        started_at=CREATED,
        completed_at=CREATED,
    )


def _seed(path):
    workflow = _workflow()
    execution = _execution(workflow)
    with Store(path) as store:
        store.put_record(Record(
            id=INPUT_ID, kind=RecordKind.OBSERVATION, payload={"value": 1},
            provenance=PROVENANCE, created_at=CREATED,
        ))
        store.put_record(Record(
            id=OUTPUT_ID, kind=RecordKind.RESULT, payload={"value": 2},
            provenance=PROVENANCE, created_at=CREATED,
        ))
        store.put_workflow_definition(workflow)
        store.put_workflow_execution(execution)
    return workflow, execution


def test_public_api_exposes_persisted_workflow_history_without_reinterpretation(tmp_path):
    path = tmp_path / "phase14.sqlite"
    workflow, execution = _seed(path)

    with Store(path, read_only=True) as store:
        assert get_workflow_definition(store, workflow.id) == workflow.to_dict()
        assert list_workflow_definitions(store) == [workflow.to_dict()]
        assert get_workflow_execution(store, execution.id) == execution.to_dict()
        assert list_workflow_executions(store) == [execution.to_dict()]
        assert list_workflow_executions(store, workflow_id=workflow.id) == [execution.to_dict()]
        assert workflow_execution_lineage(store, execution.id) == execution.lineage_dict()


def test_public_execution_lineage_excludes_execution_identity_and_timestamps(tmp_path):
    path = tmp_path / "phase14.sqlite"
    workflow, execution = _seed(path)

    with Store(path, read_only=True) as store:
        lineage = workflow_execution_lineage(store, execution.id)

    assert "id" not in lineage
    assert "started_at" not in lineage
    assert "completed_at" not in lineage
    assert lineage["workflow_id"] == workflow.id
    assert lineage["step_results"][1]["input_ids"] == [OUTPUT_ID]


def test_public_api_preserves_failed_execution_history(tmp_path):
    path = tmp_path / "phase14.sqlite"
    workflow = WorkflowDefinition(
        id=WORKFLOW_ID,
        name="Public failure fixture",
        method="phase14-failure",
        method_version="1",
        input_ids=(INPUT_ID,),
        steps=(
            WorkflowStep("step-one", "first", "phase14-first", "1", (INPUT_ID,)),
            WorkflowStep("step-two", "missing", "phase14-missing", "7"),
        ),
    )
    execution = WorkflowExecution(
        id=EXECUTION_ID,
        workflow_id=workflow.id,
        workflow_method=workflow.method,
        workflow_method_version=workflow.method_version,
        status="failed",
        step_results=(
            WorkflowStepResult(
                step_id="step-one", method="phase14-first", method_version="1",
                status="completed", input_ids=(INPUT_ID,), output_ids=(OUTPUT_ID,),
            ),
            WorkflowStepResult(
                step_id="step-two", method="phase14-missing", method_version="7",
                status="failed", input_ids=(OUTPUT_ID,), output_ids=(),
                error="no executor declared",
            ),
        ),
        started_at=CREATED,
    )
    with Store(path) as store:
        store.put_record(Record(
            id=INPUT_ID, kind=RecordKind.OBSERVATION, payload={"value": 1},
            provenance=PROVENANCE, created_at=CREATED,
        ))
        store.put_record(Record(
            id=OUTPUT_ID, kind=RecordKind.RESULT, payload={"value": 2},
            provenance=PROVENANCE, created_at=CREATED,
        ))
        store.put_workflow_definition(workflow)
        store.put_workflow_execution(execution)

    with Store(path, read_only=True) as store:
        public = get_workflow_execution(store, execution.id)

    assert public["status"] == "failed"
    assert public["step_results"][0]["status"] == "completed"
    assert public["step_results"][1]["status"] == "failed"
    assert public["step_results"][1]["error"] == "no executor declared"


def test_cli_execution_inspection_is_read_only(tmp_path, capsys):
    path = tmp_path / "phase14.sqlite"
    workflow, execution = _seed(path)

    from episteme.__main__ import main
    import sys

    original = sys.argv
    try:
        sys.argv = ["python -m episteme", "--store", str(path), "execution", execution.id]
        assert main() == 0
    finally:
        sys.argv = original

    assert json.loads(capsys.readouterr().out) == execution.to_dict()

    with Store(path, read_only=True) as store:
        assert store.get_workflow_definition(workflow.id) == workflow
        assert store.get_workflow_execution(execution.id) == execution


def test_http_exposes_workflow_and_execution_history_read_only(tmp_path):
    path = tmp_path / "phase14.sqlite"
    workflow, execution = _seed(path)
    server = create_http_server(path, port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        base = f"http://{host}:{port}/api/v1"

        with urlopen(f"{base}/workflows/{workflow.id}") as response:
            assert json.loads(response.read()) == workflow.to_dict()

        with urlopen(f"{base}/workflows") as response:
            assert json.loads(response.read()) == [workflow.to_dict()]

        with urlopen(f"{base}/executions/{execution.id}") as response:
            assert json.loads(response.read()) == execution.to_dict()

        with urlopen(f"{base}/executions?workflow_id={workflow.id}") as response:
            assert json.loads(response.read()) == [execution.to_dict()]

        with urlopen(f"{base}/executions/{execution.id}/lineage") as response:
            assert json.loads(response.read()) == execution.lineage_dict()

        with Store(path, read_only=True) as store:
            assert store.get_workflow_definition(workflow.id) == workflow
            assert store.get_workflow_execution(execution.id) == execution
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
