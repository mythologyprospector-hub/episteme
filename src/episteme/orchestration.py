"""Phase 12 finite workflow orchestration.

This module coordinates existing Episteme operations without introducing a new
epistemic object or persistence model. Workflow artifacts are execution
metadata: they describe what ran, what it consumed, and what it produced.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping
from uuid import uuid4

from .model import canonical_json


@dataclass(frozen=True, slots=True)
class WorkflowStep:
    """A declared finite operation in a workflow."""

    id: str
    name: str
    method: str
    method_version: str
    input_ids: tuple[str, ...] = ()
    parameters: Mapping[str, Any] | None = None
    assumptions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.name.strip():
            raise ValueError("workflow step id and name must be non-empty")
        if not self.method.strip() or not self.method_version.strip():
            raise ValueError("workflow step method and version must be non-empty")
        if self.parameters is not None:
            canonical_json(self.parameters)
        for value in self.assumptions:
            if not isinstance(value, str) or not value.strip():
                raise ValueError("workflow assumptions must be non-empty strings")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "method": self.method,
            "method_version": self.method_version,
            "input_ids": list(self.input_ids),
            "parameters": dict(self.parameters) if self.parameters is not None else None,
            "assumptions": list(self.assumptions),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "WorkflowStep":
        return cls(
            id=data["id"], name=data["name"], method=data["method"],
            method_version=data["method_version"],
            input_ids=tuple(data.get("input_ids", ())),
            parameters=data.get("parameters"),
            assumptions=tuple(data.get("assumptions", ())),
        )


@dataclass(frozen=True, slots=True)
class WorkflowDefinition:
    """A declared finite workflow procedure."""

    id: str
    name: str
    method: str
    method_version: str
    input_ids: tuple[str, ...]
    steps: tuple[WorkflowStep, ...]
    assumptions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.name.strip():
            raise ValueError("workflow id and name must be non-empty")
        if not self.method.strip() or not self.method_version.strip():
            raise ValueError("workflow method and version must be non-empty")
        if not self.steps:
            raise ValueError("workflow requires at least one step")
        step_ids = [step.id for step in self.steps]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("workflow step ids must be unique")
        for value in self.assumptions:
            if not isinstance(value, str) or not value.strip():
                raise ValueError("workflow assumptions must be non-empty strings")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "method": self.method,
            "method_version": self.method_version,
            "input_ids": list(self.input_ids),
            "steps": [step.to_dict() for step in self.steps],
            "assumptions": list(self.assumptions),
        }

    def lineage_dict(self) -> dict[str, Any]:
        """Return deterministic procedure semantics, excluding execution metadata."""
        return self.to_dict()

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "WorkflowDefinition":
        return cls(
            id=data["id"], name=data["name"], method=data["method"],
            method_version=data["method_version"],
            input_ids=tuple(data.get("input_ids", ())),
            steps=tuple(WorkflowStep.from_dict(item) for item in data["steps"]),
            assumptions=tuple(data.get("assumptions", ())),
        )


@dataclass(frozen=True, slots=True)
class WorkflowStepResult:
    """Execution metadata for one workflow step."""

    step_id: str
    method: str
    method_version: str
    status: str
    input_ids: tuple[str, ...]
    output_ids: tuple[str, ...]
    error: str | None = None

    def __post_init__(self) -> None:
        if not self.method.strip() or not self.method_version.strip():
            raise ValueError("workflow step result method and version must be non-empty")
        if self.status not in {"completed", "failed"}:
            raise ValueError("workflow step status must be completed or failed")
        if self.status == "failed" and not self.error:
            raise ValueError("failed workflow step requires an error")
        if self.status == "completed" and self.error is not None:
            raise ValueError("completed workflow step cannot carry an error")

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "method": self.method,
            "method_version": self.method_version,
            "status": self.status,
            "input_ids": list(self.input_ids),
            "output_ids": list(self.output_ids),
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "WorkflowStepResult":
        return cls(
            step_id=data["step_id"], method=data["method"],
            method_version=data["method_version"], status=data["status"],
            input_ids=tuple(data.get("input_ids", ())),
            output_ids=tuple(data.get("output_ids", ())),
            error=data.get("error"),
        )


@dataclass(frozen=True, slots=True)
class WorkflowExecution:
    """Inspectable result of executing a declared workflow."""

    id: str
    workflow_id: str
    workflow_method: str
    workflow_method_version: str
    status: str
    step_results: tuple[WorkflowStepResult, ...]
    started_at: str
    completed_at: str | None = None

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.workflow_id.strip():
            raise ValueError("workflow execution ids must be non-empty")
        if self.status not in {"completed", "failed"}:
            raise ValueError("workflow execution status must be completed or failed")
        if not self.step_results:
            raise ValueError("workflow execution requires step results")
        if self.status == "completed" and self.step_results[-1].status == "failed":
            raise ValueError("completed workflow cannot end with a failed step")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "workflow_method": self.workflow_method,
            "workflow_method_version": self.workflow_method_version,
            "status": self.status,
            "step_results": [result.to_dict() for result in self.step_results],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }

    def lineage_dict(self) -> dict[str, Any]:
        """Return execution lineage without fresh execution timestamps/identity."""
        return {
            "workflow_id": self.workflow_id,
            "workflow_method": self.workflow_method,
            "workflow_method_version": self.workflow_method_version,
            "status": self.status,
            "step_results": [result.to_dict() for result in self.step_results],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "WorkflowExecution":
        return cls(
            id=data["id"], workflow_id=data["workflow_id"],
            workflow_method=data["workflow_method"],
            workflow_method_version=data["workflow_method_version"],
            status=data["status"],
            step_results=tuple(
                WorkflowStepResult.from_dict(item) for item in data["step_results"]
            ),
            started_at=data["started_at"], completed_at=data.get("completed_at"),
        )


StepExecutor = Callable[[WorkflowStep, tuple[str, ...]], tuple[str, ...]]


def run_workflow(
    workflow: WorkflowDefinition,
    executors: Mapping[str, StepExecutor],
    *,
    started_at: str,
) -> WorkflowExecution:
    """Execute a declared finite workflow in declared order.

    Executors are adapters over existing Episteme operations. They receive the
    exact effective input identifiers recorded for the step and return
    identifiers of artifacts produced by the operation. The runner records
    execution metadata only and never changes epistemic status.
    """
    results: list[WorkflowStepResult] = []
    previous_output_ids: tuple[str, ...] = ()
    for step in workflow.steps:
        effective_input_ids = step.input_ids or previous_output_ids
        executor = executors.get(step.name)
        if executor is None:
            result = WorkflowStepResult(
                step_id=step.id,
                method=step.method,
                method_version=step.method_version,
                status="failed",
                input_ids=effective_input_ids,
                output_ids=(),
                error=f"no executor declared for workflow step: {step.name}",
            )
            results.append(result)
            return WorkflowExecution(
                id=str(uuid4()),
                workflow_id=workflow.id,
                workflow_method=workflow.method,
                workflow_method_version=workflow.method_version,
                status="failed",
                step_results=tuple(results),
                started_at=started_at,
            )
        try:
            output_ids = tuple(executor(step, effective_input_ids))
        except Exception as exc:
            result = WorkflowStepResult(
                step_id=step.id,
                method=step.method,
                method_version=step.method_version,
                status="failed",
                input_ids=effective_input_ids,
                output_ids=(),
                error=f"{type(exc).__name__}: {exc}",
            )
            results.append(result)
            return WorkflowExecution(
                id=str(uuid4()),
                workflow_id=workflow.id,
                workflow_method=workflow.method,
                workflow_method_version=workflow.method_version,
                status="failed",
                step_results=tuple(results),
                started_at=started_at,
            )
        previous_output_ids = output_ids
        results.append(
            WorkflowStepResult(
                step_id=step.id,
                method=step.method,
                method_version=step.method_version,
                status="completed",
                input_ids=effective_input_ids,
                output_ids=output_ids,
            )
        )

    return WorkflowExecution(
        id=str(uuid4()),
        workflow_id=workflow.id,
        workflow_method=workflow.method,
        workflow_method_version=workflow.method_version,
        status="completed",
        step_results=tuple(results),
        started_at=started_at,
        completed_at=started_at,
    )
