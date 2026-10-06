from episteme.acquisition import AcquisitionResponse
from episteme.autonomy import (
    DiscoveryAction,
    EvidenceRequestRuntime,
    PlannerActionError,
    run_autonomous_discovery,
)
from episteme.capture import CaptureOutcome
from episteme.store import Store
from episteme.public import get_captured_content


def test_evidence_request_uses_host_owned_provider_and_existing_capture(tmp_path):
    store = Store(tmp_path / "episteme.db")
    seen = []

    def provider(request):
        seen.append(request)
        return AcquisitionResponse(
            status=200,
            media_type="text/plain",
            source_version="v1",
            content=b"grounded-looking text is still only captured",
            outcome=CaptureOutcome.COMPLETE,
        )

    runtime = EvidenceRequestRuntime(
        provider=provider,
        allowed_source_ids=("approved-source",),
        allowed_methods=("approved-fetch",),
        max_resource_length=100,
    )

    class Planner:
        def choose(self, context):
            return DiscoveryAction(
                kind="request_evidence",
                evidence_request={
                    "source_id": "approved-source",
                    "requested_resource": "resource-1",
                    "request_parameters": {"query": "bounded"},
                    "acquisition_method": "approved-fetch",
                    "acquisition_method_version": "1",
                },
                rationale="The current bounded investigation requires this external representation.",
            )

    result = run_autonomous_discovery(
        store,
        Planner(),
        grounded_input_ids=(),
        started_at="2026-10-06T12:00:00Z",
        max_steps=1,
        evidence_request_runtime=runtime,
    )

    assert result.status == "budget_exhausted"
    assert len(result.steps) == 1
    assert result.steps[0].action.kind == "request_evidence"
    assert seen[0].source_id == "approved-source"
    captures = tuple(store.iter_captured_representations())
    assert len(captures) == 1
    assert captures[0].outcome is CaptureOutcome.COMPLETE
    assert get_captured_content(store, captures[0].id) == b"grounded-looking text is still only captured"


def test_evidence_request_cannot_select_an_unapproved_source(tmp_path):
    store = Store(tmp_path / "episteme.db")

    runtime = EvidenceRequestRuntime(
        provider=lambda request: (_ for _ in ()).throw(AssertionError("provider must not run")),
        allowed_source_ids=("approved-source",),
        allowed_methods=("approved-fetch",),
    )

    class Planner:
        def choose(self, context):
            return DiscoveryAction(
                kind="request_evidence",
                evidence_request={
                    "source_id": "not-approved",
                    "requested_resource": "resource-1",
                    "request_parameters": {},
                    "acquisition_method": "approved-fetch",
                    "acquisition_method_version": "1",
                },
                rationale="The request should be rejected before external acquisition.",
            )

    result = run_autonomous_discovery(
        store,
        Planner(),
        grounded_input_ids=(),
        started_at="2026-10-06T12:00:00Z",
        max_steps=1,
        max_retries_per_step=0,
        evidence_request_runtime=runtime,
    )

    assert result.status == "failed"
    assert "source_id is not allowed" in result.stop_reason
    assert tuple(store.iter_captured_representations()) == ()


def test_evidence_request_requires_bounded_request_shape():
    action = DiscoveryAction(
        kind="request_evidence",
        evidence_request={"source_id": "x"},
        rationale="request",
    )
    runtime = EvidenceRequestRuntime(
        provider=lambda request: None,
        allowed_source_ids=("x",),
        allowed_methods=("m",),
    )
    store = Store(":memory:")

    try:
        runtime.request(store, action.evidence_request, captured_at="2026-10-06T12:00:00Z")
    except PlannerActionError as exc:
        assert "requested_resource" in str(exc)
    else:
        raise AssertionError("invalid request must be rejected")
