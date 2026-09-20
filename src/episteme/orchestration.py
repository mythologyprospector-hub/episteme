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
            "parameters": dict(self.parameters or {}),
            "assumptions": list(self.assumptions),
        }


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


@dataclass(frozen=True, slots=True)
class WorkflowStepResult:
    """Execution metadata for one workflow step."""

    step_id: str
    status: str
    input_ids: tuple[str, ...]
    output_ids: tuple[str, ...]
    error: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {"completed", "failed"}:
            raise ValueError("workflow step status must be completed or failed")
        if self.status == "failed" and not self.error:
            raise ValueError("failed workflow step requires an error")
        if self.status == "completed" and self.error is not None:
            raise ValueError("completed workflow step cannot carry an error")

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "status": self.status,
            "input_ids": list(self.input_ids),
            "output_ids": list(self.output_ids),
            "error": self.error,
        }


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


StepExecutor = Callable[[WorkflowStep], tuple[str, ...]]


def run_workflow(
    workflow: WorkflowDefinition,
    executors: Mapping[str, StepExecutor],
    *,
    started_at: str,
) -> WorkflowExecution:
    """Execute a declared finite workflow in declared order.

    Executors are adapters over existing Episteme operations. They return
    identifiers of artifacts produced by the operation. The runner records
    execution metadata only and never changes epistemic status.
    """
    results: list[WorkflowStepResult] = []
    for step in workflow.steps:
        executor = executors.get(step.name)
        if executor is None:
            result = WorkflowStepResult(
                step_id=step.id,
                status="failed",
                input_ids=step.input_ids,
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
            output_ids = tuple(executor(step))
        except Exception as exc:
            result = WorkflowStepResult(
                step_id=step.id,
                status="failed",
                input_ids=step.input_ids,
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
        results.append(
            WorkflowStepResult(
                step_id=step.id,
                status="completed",
                input_ids=step.input_ids,
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
