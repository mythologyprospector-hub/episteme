"""Phase 24 proof of acquisition as a workflow operation."""

from episteme import Store
from episteme.acquisition import AcquisitionRequest, AcquisitionResponse, acquire
from episteme.capture import CaptureOutcome
from episteme.orchestration import WorkflowDefinition, WorkflowStep, run_workflow

CREATED = "2026-09-20T00:00:00Z"
CAPTURE_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


def test_acquisition_can_execute_as_workflow_step_and_persist_capture(tmp_path):
    path = tmp_path / "phase24.sqlite"
    capture_root = tmp_path / "captures"
    request = AcquisitionRequest(
        source_id="crossref",
        requested_resource="https://api.crossref.org/v1/works",
        request_parameters={"rows": 1},
        acquisition_method="crossref-rest",
        acquisition_method_version="1",
    )

    def provider(received):
        assert received == request
        return AcquisitionResponse(
            status=200,
            media_type="application/json",
            source_version="etag-phase24",
            content=b'{"message":{"items":[]}}',
            outcome=CaptureOutcome.COMPLETE,
        )

    workflow = WorkflowDefinition(
        id="phase24-acquisition",
        name="Bounded acquisition workflow",
        method="phase24-acquisition-workflow",
        method_version="1",
        input_ids=(),
        steps=(WorkflowStep(
            "step-acquire", "acquire", "crossref-rest", "1",
            parameters={"source_id": "crossref", "rows": 1},
        ),),
    )

    with Store(path, capture_root=capture_root) as store:
        store.put_workflow_definition(workflow)

        def acquire_step(step, input_ids):
            assert input_ids == ()
            capture = acquire(request, provider, store, captured_at=CREATED, capture_id=CAPTURE_ID)
            return (capture.id,)

        execution = run_workflow(workflow, {"acquire": acquire_step}, started_at=CREATED)
        assert execution.status == "completed"
        assert execution.step_results[0].output_ids == (CAPTURE_ID,)
        store.put_workflow_execution(execution)
        assert store.read_captured_content(CAPTURE_ID) == b'{"message":{"items":[]}}'
        assert store.get_workflow_execution(execution.id) == execution


def test_failed_acquisition_as_workflow_step_preserves_acquisition_failure(tmp_path):
    path = tmp_path / "phase24-failure.sqlite"
    capture_root = tmp_path / "captures"
    request = AcquisitionRequest(
        source_id="crossref",
        requested_resource="https://api.crossref.org/v1/works",
        request_parameters={"rows": 1},
        acquisition_method="crossref-rest",
        acquisition_method_version="1",
    )

    def provider(_):
        raise TimeoutError("provider timeout")

    workflow = WorkflowDefinition(
        id="phase24-acquisition-failure",
        name="Failed acquisition workflow",
        method="phase24-acquisition-failure",
        method_version="1",
        input_ids=(),
        steps=(WorkflowStep("step-acquire", "acquire", "crossref-rest", "1"),),
    )

    with Store(path, capture_root=capture_root) as store:
        store.put_workflow_definition(workflow)

        def acquire_step(step, input_ids):
            capture = acquire(request, provider, store, captured_at=CREATED, capture_id=CAPTURE_ID)
            return (capture.id,) if capture.outcome is CaptureOutcome.COMPLETE else ()

        execution = run_workflow(workflow, {"acquire": acquire_step}, started_at=CREATED)
        assert execution.status == "completed"
        assert execution.step_results[0].output_ids == ()
        captures = list(store.iter_captured_representations())
        assert len(captures) == 1
        assert captures[0].outcome is CaptureOutcome.FAILED
        assert captures[0].error == "TimeoutError: provider timeout"
        store.put_workflow_execution(execution)
