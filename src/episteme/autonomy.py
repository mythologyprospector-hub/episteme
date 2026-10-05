"""Bounded planner-driven discovery control.

The planner chooses among a small, explicit action vocabulary. It never receives
direct access to the Store and cannot execute arbitrary code. This module is
control-plane machinery, not an epistemic authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Protocol

from .discovery import question_from_finding
from .model import (DiscoveryFindingKind, ExperimentProposal, KnowledgeStateConsequence, KnowledgeStateConsequenceKind, KnowledgeStateTargetKind, Prediction, PredictionEvaluation)
from uuid import uuid4
from .proposals import (
    propose_candidate_discrimination_experiment,
    propose_discriminating_prediction,
    propose_hypothesis,
)


@dataclass(frozen=True, slots=True)
class DiscoveryAction:
    kind: str
    target_ids: tuple[str, ...] = ()
    statement: str | None = None
    consequence: str | None = None
    consequences: tuple[str, ...] = ()
    conditions: str | None = None
    objective: str | None = None
    proposed_observation: str | None = None
    discrimination_basis: str | None = None
    rationale: str = ""

    def __post_init__(self) -> None:
        if self.kind not in {"question", "hypothesis", "prediction", "experiment", "stop"}:
            raise ValueError(f"unknown discovery action: {self.kind}")
        if not self.rationale.strip():
            raise ValueError("discovery action requires a rationale")


@dataclass(frozen=True, slots=True)
class DiscoveryContext:
    grounded_input_ids: tuple[str, ...]
    findings: tuple[Mapping[str, Any], ...]
    hypotheses: tuple[Mapping[str, Any], ...]
    predictions: tuple[Mapping[str, Any], ...]
    experiments: tuple[Mapping[str, Any], ...]
    actions_taken: tuple[DiscoveryAction, ...]
    evaluations: tuple[Mapping[str, Any], ...] = ()
    consequences: tuple[Mapping[str, Any], ...] = ()
    feedback: tuple[str, ...] = ()


class Planner(Protocol):
    def choose(self, context: DiscoveryContext) -> DiscoveryAction:
        """Choose exactly one bounded next action from the supplied context."""


class ExperimentExecutor(Protocol):
    def execute(
        self,
        store: Any,
        proposal: ExperimentProposal,
        *,
        input_ids: tuple[str, ...],
        created_at: str,
    ) -> Any:
        """Execute the explicitly bound experiment operation."""


class ExperimentEvaluator(Protocol):
    def evaluate(
        self,
        store: Any,
        result: Any,
        proposal: ExperimentProposal,
        predictions: tuple[Prediction, ...],
        *,
        comparison_conditions: str,
        created_at: str,
    ) -> tuple[PredictionEvaluation, ...]:
        """Evaluate the result using explicitly bound executable semantics."""


@dataclass(frozen=True, slots=True)
class ExperimentRuntime:
    """Explicit runtime binding for executing and evaluating planner proposals.

    The planner can propose an experiment, but it cannot choose this executor,
    evaluator, their configuration, or the grounded inputs they receive.
    """

    executor: ExperimentExecutor
    evaluator_factory: Callable[[ExperimentProposal, tuple[Prediction, ...]], ExperimentEvaluator]
    comparison_conditions: str = ""


@dataclass(frozen=True, slots=True)
class DiscoveryStep:
    action: DiscoveryAction
    output_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DiscoveryRun:
    status: str
    steps: tuple[DiscoveryStep, ...]
    stop_reason: str | None = None


def _finding_view(finding: Any) -> dict[str, Any]:
    return {
        "id": finding.id,
        "kind": finding.kind.value,
        "title": finding.title,
        "description": finding.description,
        "input_ids": tuple(finding.input_ids),
        "context_ids": tuple(finding.context_ids),
    }


def _hypothesis_view(item: Any) -> dict[str, Any]:
    return {
        "id": item.id,
        "statement": item.statement,
        "finding_ids": tuple(item.finding_ids),
        "input_ids": tuple(item.input_ids),
    }


def _prediction_view(item: Any) -> dict[str, Any]:
    return {
        "id": item.id,
        "source_id": item.source_id,
        "consequence": item.consequence,
        "conditions": item.conditions,
        "comparison_hypothesis_ids": tuple(item.comparison_hypothesis_ids),
    }


def _evaluation_view(item: Any) -> dict[str, Any]:
    return {"id": item.id, "result_id": item.result_id, "prediction_id": item.prediction_id, "experiment_proposal_id": item.experiment_proposal_id, "outcome": item.outcome.value}


def _consequence_view(item: Any) -> dict[str, Any]:
    return {"id": item.id, "evaluation_ids": tuple(item.evaluation_ids), "target_kind": item.target_kind.value, "target_id": item.target_id, "consequence": item.consequence.value}


def _experiment_view(item: Any) -> dict[str, Any]:
    return {
        "id": item.id,
        "prediction_ids": tuple(item.prediction_ids),
        "objective": item.objective,
        "proposed_observation": item.proposed_observation,
        "discrimination_basis": item.discrimination_basis,
    }


def build_context(
    store: Any,
    grounded_input_ids: tuple[str, ...],
    actions_taken: tuple[DiscoveryAction, ...],
    feedback: tuple[str, ...] = (),
) -> DiscoveryContext:
    return DiscoveryContext(
        grounded_input_ids=tuple(grounded_input_ids),
        findings=tuple(_finding_view(item) for item in store.iter_discovery_findings()),
        hypotheses=tuple(_hypothesis_view(item) for item in store.iter_hypotheses()),
        predictions=tuple(_prediction_view(item) for item in store.iter_predictions()),
        experiments=tuple(_experiment_view(item) for item in store.iter_experiment_proposals()),
        evaluations=tuple(_evaluation_view(item) for item in store.iter_prediction_evaluations()),
        consequences=tuple(_consequence_view(item) for item in store.iter_knowledge_state_consequences()),
        actions_taken=actions_taken,
    )


def _require(value: str | None, field: str) -> str:
    if value is None or not value.strip():
        raise ValueError(f"{field} is required for this discovery action")
    return value


def execute_action(store: Any, action: DiscoveryAction, *, created_at: str) -> tuple[str, ...]:
    """Validate and execute one action using existing Episteme primitives."""
    if action.kind == "stop":
        return ()

    if not action.target_ids:
        raise ValueError(f"{action.kind} action requires target_ids")

    if action.kind == "question":
        if len(action.target_ids) != 1:
            raise ValueError("question action requires exactly one finding")
        finding = store.get_discovery_finding(action.target_ids[0])
        if finding is None:
            raise ValueError("question target finding does not exist")
        if finding.kind not in {DiscoveryFindingKind.GAP, DiscoveryFindingKind.TENSION}:
            raise ValueError("question target must be a gap or tension finding")
        question = question_from_finding(finding, created_at)
        store.put_discovery_finding(question)
        return (question.id,)

    if action.kind == "hypothesis":
        if len(action.target_ids) != 1:
            raise ValueError("hypothesis action requires exactly one finding")
        statement = _require(action.statement, "statement")
        finding = store.get_discovery_finding(action.target_ids[0])
        if finding is None:
            raise ValueError("hypothesis target finding does not exist")
        hypothesis = propose_hypothesis(
            statement=statement,
            finding_ids=(finding.id,),
            input_ids=finding.input_ids,
            method="planner-driven-hypothesis",
            method_version="1",
            rationale=action.rationale,
            created_at=created_at,
        )
        store.put_hypothesis(hypothesis)
        return (hypothesis.id,)

    if action.kind == "prediction":
        if len(action.target_ids) < 2:
            raise ValueError("prediction action requires at least two hypothesis ids")
        conditions = _require(action.conditions, "conditions")
        consequences = action.consequences
        if not consequences:
            consequence = _require(action.consequence, "consequence")
            consequences = tuple(consequence for _ in action.target_ids)
        if len(consequences) != len(action.target_ids):
            raise ValueError("prediction consequences must match hypothesis targets")
        outputs = []
        for candidate_id, consequence in zip(action.target_ids, consequences):
            prediction = propose_discriminating_prediction(
                store,
                candidate_id=candidate_id,
                competing_candidate_ids=action.target_ids,
                consequence=consequence,
                conditions=conditions,
                method="planner-driven-prediction",
                method_version="1",
                rationale=action.rationale,
                created_at=created_at,
            )
            store.put_prediction(prediction)
            outputs.append(prediction.id)
        return tuple(outputs)

    if action.kind == "experiment":
        if len(action.target_ids) < 2:
            raise ValueError("experiment action requires at least two prediction ids")
        proposal = propose_candidate_discrimination_experiment(
            store,
            prediction_ids=action.target_ids,
            objective=_require(action.objective, "objective"),
            proposed_observation=_require(action.proposed_observation, "proposed_observation"),
            discrimination_basis=_require(action.discrimination_basis, "discrimination_basis"),
            conditions=_require(action.conditions, "conditions"),
            method="planner-driven-experiment",
            method_version="1",
            rationale=action.rationale,
            created_at=created_at,
        )
        store.put_experiment_proposal(proposal)
        return (proposal.id,)

    raise ValueError(f"unsupported discovery action: {action.kind}")


def _execute_experiment_cycle(
    store: Any,
    proposal: ExperimentProposal,
    *,
    grounded_input_ids: tuple[str, ...],
    runtime: ExperimentRuntime,
    created_at: str,
) -> tuple[str, ...]:
    """Execute, evaluate, and record consequences for one persisted proposal.

    The executor and evaluator are explicit runtime bindings supplied to the
    bounded driver. The planner never chooses executable semantics, and the
    evaluator never asks the planner or an LLM to interpret a result.
    """
    result = runtime.executor.execute(
        store,
        proposal,
        input_ids=grounded_input_ids,
        created_at=created_at,
    )
    predictions = tuple(
        prediction
        for prediction_id in proposal.prediction_ids
        if (prediction := store.get_prediction(prediction_id)) is not None
    )
    if len(predictions) != len(proposal.prediction_ids):
        raise ValueError("experiment proposal references missing predictions")

    evaluator = runtime.evaluator_factory(proposal, predictions)
    evaluations = evaluator.evaluate(
        store,
        result,
        proposal,
        predictions,
        comparison_conditions=runtime.comparison_conditions,
        created_at=created_at,
    )
    consequence_ids = record_prediction_consequences(
        store,
        evaluations,
        created_at=created_at,
    )
    return (
        proposal.id,
        result.id,
        *(evaluation.id for evaluation in evaluations),
        *consequence_ids,
    )


def record_prediction_consequences(
    store: Any,
    evaluations: tuple[PredictionEvaluation, ...],
    *,
    created_at: str,
) -> tuple[str, ...]:
    """Record contextual consequences from deterministic evaluations."""
    outputs: list[str] = []
    for evaluation in evaluations:
        if evaluation.outcome.value == "consistent":
            kind = KnowledgeStateConsequenceKind.SUPPORTS
        elif evaluation.outcome.value == "inconsistent":
            kind = KnowledgeStateConsequenceKind.CONTRADICTS
        else:
            kind = KnowledgeStateConsequenceKind.LEAVES_UNRESOLVED
        item = KnowledgeStateConsequence(
            id=str(uuid4()),
            evaluation_ids=(evaluation.id,),
            target_kind=KnowledgeStateTargetKind.PREDICTION,
            target_id=evaluation.prediction_id,
            consequence=kind,
            assumptions=evaluation.assumptions,
            rationale="Deterministic bookkeeping consequence; not a claim of truth.",
            method="prediction-evaluation-consequence",
            method_version="1",
            created_at=created_at,
        )
        store.put_knowledge_state_consequence(item)
        outputs.append(item.id)
    return tuple(outputs)


def run_autonomous_discovery(
    store: Any,
    planner: Planner,
    *,
    grounded_input_ids: tuple[str, ...],
    started_at: str,
    max_steps: int = 12,
    experiment_runtime: ExperimentRuntime | None = None,
    max_retries_per_step: int = 2,
) -> DiscoveryRun:
    """Run a finite planner-steered investigation until stop or a hard budget.

    Invalid planner actions are fed back to the planner for bounded correction
    rather than terminating the entire run. No invalid action is persisted.
    """
    if max_steps < 1:
        raise ValueError("max_steps must be positive")
    if max_retries_per_step < 0:
        raise ValueError("max_retries_per_step must be non-negative")

    actions: list[DiscoveryAction] = []
    steps: list[DiscoveryStep] = []
    feedback: list[str] = []

    for _ in range(max_steps):
        for attempt in range(max_retries_per_step + 1):
            context = build_context(
                store,
                grounded_input_ids,
                tuple(actions),
                tuple(feedback),
            )

            try:
                action = planner.choose(context)
                feedback.clear()
                if not isinstance(action, DiscoveryAction):
                    raise TypeError("planner must return DiscoveryAction")
                if action.kind == "stop":
                    return DiscoveryRun(
                        status="stopped",
                        steps=tuple(steps),
                        stop_reason=action.rationale,
                    )

                output_ids = execute_action(store, action, created_at=started_at)
                if action.kind == "experiment" and experiment_runtime is not None:
                    proposal = store.get_experiment_proposal(output_ids[0])
                    if proposal is None:
                        raise ValueError("experiment action did not persist its proposal")
                    output_ids = _execute_experiment_cycle(
                        store,
                        proposal,
                        grounded_input_ids=grounded_input_ids,
                        runtime=experiment_runtime,
                        created_at=started_at,
                    )

            except (TypeError, ValueError) as exc:
                if attempt >= max_retries_per_step:
                    return DiscoveryRun(
                        status="failed",
                        steps=tuple(steps),
                        stop_reason=f"planner action failed after {attempt + 1} attempts: {exc}",
                    )
                feedback.append(
                    f"The previous proposed action was rejected: {exc}. "
                    "Choose a corrected action that satisfies the supplied action contract."
                )
                continue

            steps.append(DiscoveryStep(action=action, output_ids=output_ids))
            actions.append(action)
            break

    return DiscoveryRun(
        status="budget_exhausted",
        steps=tuple(steps),
        stop_reason=f"maximum discovery step budget reached: {max_steps}",
    )