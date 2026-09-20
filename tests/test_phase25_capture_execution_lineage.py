"""Phase 25 proof of capture-to-execution lineage."""

import json
import sys
from threading import Thread
from urllib.request import urlopen

from episteme import (
    CaptureOutcome,
    CapturedRepresentation,
    Store,
    WorkflowDefinition,
    WorkflowStep,
    list_workflow_executions_for_capture,
    run_workflow,
)
from episteme.http_api import create_http_server

CAPTURE_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
CAPTURED_AT = "2026-09-20T00:00:00Z"


def _seed(tmp_path):
    path = tmp_path / "phase25.sqlite"
    root = tmp_path / "captures"
    content = b'{"message":{"items":[]}}'
    import hashlib
    digest = hashlib.sha256(content).hexdigest()
    capture = CapturedRepresentation(
        CAPTURE_ID, "crossref", "https://api.crossref.org/v1/works",
        {"rows": 1}, CAPTURED_AT, 200, "application/json", "etag-25",
        digest, f"sha256/{digest}", "crossref-rest", "1",
        CaptureOutcome.COMPLETE, None, 2,
    )
    workflow = WorkflowDefinition(
        "phase25-workflow", "Capture lineage proof", "phase25", "1", (), (
            WorkflowStep("step", "acquire", "crossref-rest", "1", {}),
        ),
    )
    with Store(path, capture_root=root) as store:
        store.put_captured_representation(capture, content=content)
        store.put_workflow_definition(workflow)

        def step(_step, _inputs):
            return (CAPTURE_ID,)

        execution = run_workflow(workflow, {"acquire": step}, started_at=CAPTURED_AT)
        store.put_workflow_execution(execution)
    return path, root, execution


def test_capture_reverse_lookup_finds_producing_execution(tmp_path):
    path, root, execution = _seed(tmp_path)
    with Store(path, read_only=True, capture_root=root) as store:
        result = list_workflow_executions_for_capture(store, CAPTURE_ID)
        assert [item["id"] for item in result] == [execution.id]


def test_capture_reverse_lookup_rejects_missing_capture(tmp_path):
    from episteme.public import PublicNotFoundError
    with Store(tmp_path / "phase25.sqlite", capture_root=tmp_path / "captures") as store:
        try:
            list_workflow_executions_for_capture(store, CAPTURE_ID)
        except PublicNotFoundError as exc:
            assert "captured representation not found" in str(exc)
        else:
            raise AssertionError("missing capture must be rejected")


def test_capture_reverse_lookup_cli_is_read_only(tmp_path):
    path, root, execution = _seed(tmp_path)
    from episteme.__main__ import main
    old = sys.argv
    try:
        sys.argv = ["episteme", "--store", str(path), "--capture-root", str(root),
                    "capture-executions", CAPTURE_ID]
        assert main() == 0
    finally:
        sys.argv = old
    with Store(path, read_only=True, capture_root=root) as store:
        assert store.get_workflow_execution(execution.id) == execution


def test_capture_reverse_lookup_http_is_read_only(tmp_path):
    path, root, execution = _seed(tmp_path)
    server = create_http_server(path, port=0, capture_root=root)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        with urlopen(f"http://{host}:{port}/api/v1/captures/{CAPTURE_ID}/executions") as response:
            body = json.loads(response.read())
            assert [item["id"] for item in body] == [execution.id]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
