"""Phase 15 proof of artifact-to-execution lineage."""

import json
from threading import Thread
from urllib.error import HTTPError
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
    list_workflow_executions_for_artifact,
)
from episteme.http_api import create_http_server


CREATED = "2026-09-20T00:00:00Z"
INPUT_ID = "11111111-1111-4111-8111-111111111111"
OUTPUT_ID = "22222222-2222-4222-8222-222222222222"
WORKFLOW_ID = "33333333-3333-4333-8333-333333333331"
EXECUTION_ID = "33333333-3333-4333-8333-333333333332"


def _workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        id=WORKFLOW_ID,
        name="Artifact lineage fixture",
        method="phase15-fixture-workflow",
        method_version="1",
        input_ids=(INPUT_ID,),
        steps=(
            WorkflowStep("step-one", "first", "phase15-first", "1", (INPUT_ID,)),
            WorkflowStep("step-two", "second", "phase15-second", "2"),
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
                method="phase15-first",
                method_version="1",
                status="completed",
                input_ids=(INPUT_ID,),
                output_ids=(OUTPUT_ID,),
            ),
            WorkflowStepResult(
                step_id="step-two",
                method="phase15-second",
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
    provenance = (
        Provenance(
            source_id="phase15-fixture",
            captured_at=CREATED,
            source_location="https://example.org/phase15",
            source_version="1",
        ),
    )
    with Store(path) as store:
        store.put_record(
            Record(
                id=INPUT_ID,
                kind=RecordKind.OBSERVATION,
                payload={"value": 1},
                provenance=provenance,
                created_at=CREATED,
            )
        )
        store.put_record(
            Record(
                id=OUTPUT_ID,
                kind=RecordKind.RESULT,
                payload={"value": 2},
                provenance=provenance,
                created_at=CREATED,
            )
        )
        store.put_workflow_definition(workflow)
        store.put_workflow_execution(execution)
    return workflow, execution


def test_artifact_lookup_returns_consuming_and_producing_executions(tmp_path):
    path = tmp_path / "phase15.sqlite"
    workflow, execution = _seed(path)

    with Store(path, read_only=True) as store:
        result = list_workflow_executions_for_artifact(store, INPUT_ID)

    assert result == [execution.to_dict()]
    assert result[0]["step_results"][0]["output_ids"] == [OUTPUT_ID]
    assert result[0]["step_results"][1]["input_ids"] == [OUTPUT_ID]
    assert workflow.id == result[0]["workflow_id"]


def test_artifact_lookup_deduplicates_one_execution_referencing_artifact_multiple_times(tmp_path):
    path = tmp_path / "phase15.sqlite"
    _, execution = _seed(path)

    with Store(path, read_only=True) as store:
        result = list_workflow_executions_for_artifact(store, OUTPUT_ID)

    assert result == [execution.to_dict()]


def test_unknown_artifact_is_not_an_empty_known_history(tmp_path):
    path = tmp_path / "phase15.sqlite"
    _seed(path)

    with Store(path, read_only=True) as store:
        try:
            list_workflow_executions_for_artifact(
                store, "99999999-9999-4999-8999-999999999999"
            )
        except ValueError as exc:
            assert str(exc).startswith("artifact not found:")
        else:
            raise AssertionError("missing artifact must be rejected")


def test_cli_artifact_execution_lookup_is_read_only(tmp_path, capsys):
    path = tmp_path / "phase15.sqlite"
    _, execution = _seed(path)

    from episteme.__main__ import main
    import sys

    original = sys.argv
    try:
        sys.argv = [
            "python -m episteme",
            "--store",
            str(path),
            "artifact-executions",
            INPUT_ID,
        ]
        assert main() == 0
    finally:
        sys.argv = original

    assert json.loads(capsys.readouterr().out) == [execution.to_dict()]


def test_http_artifact_execution_lookup_is_read_only(tmp_path):
    path = tmp_path / "phase15.sqlite"
    _, execution = _seed(path)
    server = create_http_server(path, port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        base = f"http://{host}:{port}/api/v1"
        with urlopen(f"{base}/artifacts/{INPUT_ID}/executions") as response:
            assert json.loads(response.read()) == [execution.to_dict()]

        with urlopen(f"{base}/artifacts/{OUTPUT_ID}/executions") as response:
            assert json.loads(response.read()) == [execution.to_dict()]

        try:
            urlopen(f"{base}/artifacts/99999999-9999-4999-8999-999999999999/executions")
        except HTTPError as exc:
            assert exc.code == 404
        else:
            raise AssertionError("missing artifact must return 404")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
