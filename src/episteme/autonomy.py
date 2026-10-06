"""Bounded planner-driven discovery control.

The planner chooses among a small, explicit action vocabulary. It never receives
direct access to the Store and cannot execute arbitrary code. This module is
control-plane machinery, not an epistemic authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Protocol

from .discovery import detect_positional_gap, question_from_finding
from .evidence_request import EvidenceRequest
from .exploration import scout_positional_records
from .exploration_bridge import admit_exploration_observation, assess_exploration_observation
from .model import Provenance
from .executor import ExecutableExperimentSpec, build_registered_experiment_runtime
from .model import (DiscoveryFindingKind, ExperimentProposal, KnowledgeStateConsequence, KnowledgeStateConsequenceKind, KnowledgeStateTargetKind, Prediction, PredictionEvaluation)
from uuid import uuid4
from .proposals import (
    propose_candidate_discrimination_experiment,
    propose_discriminating_prediction,
    propose_hypothesis,
)


class EvidenceRequestRuntime(Protocol):
    """Host-owned binding for bounded external evidence acquisition."""

    def request_evidence(
        self, store: Any, request: EvidenceRequest, *, created_at: str
    ) -> Any:
        """Execute one validated evidence request through host-owned policy."""


class ExplorationRuntime(Protocol):
    """Host-owned binding for bounded exploration."""

    def scout(self, store: Any, *, created_at: str) -> Any:
        """Run one preconfigured bounded scout operation."""


class StructuralDiscoveryRuntime(Protocol):
    """Host-owned binding for one bounded structural discovery operation."""

    def discover(self, store: Any, *, created_at: str) -> Any:
        """Run one preconfigured structural discovery operation."""


@dataclass(frozen=True, slots=True)
class PositionalGapDiscoveryRuntime:
    """Host-owned configuration for bounded positional gap discovery."""

    input_ids: tuple[str, ...]
    position_key: str
    step: float

    def discover(self, store: Any, *, created_at: str) -> Any:
        finding = detect_positional_gap(
            store,
            self.input_ids,
            self.position_key,
            self.step,
            created_at,
        )
        if finding is None:
            raise PlannerActionError("bounded structural discovery found no gap")
        store.put_discovery_finding(finding)
        return finding


@dataclass(frozen=True, slots=True)
class PositionalExplorationRuntime:
    """Host-owned configuration for the bounded positional scout."""

    input_ids: tuple[str, ...]
    position_key: str
    max_records: int

    def scout(self, store: Any, *, created_at: str) -> Any:
        return scout_positional_records(
            store,
            self.input_ids,
            self.position_key,
            max_records=self.max_records,
            created_at=created_at,
        )


@dataclass(frozen=True, slots=True)
class ExplorationAssessmentRuntime:
    """Host-owned policy for assessing one bounded exploration observation."""

    allowed_input_ids: tuple[str, ...]
    accepted: bool
    method: str
    method_version: str
    rationale: str
    provenance: tuple[Provenance, ...]

    def assess(self, store: Any, observation_id: str, *, created_at: str) -> Any:
        observation = store.get_exploration_observation(observation_id)
        if observation is None:
            raise PlannerActionError("exploration observation does not exist")
        if not set(observation.input_ids).issubset(self.allowed_input_ids):
            raise PlannerActionError("observation inputs are outside the host-owned assessment scope")
        return assess_exploration_observation(
            store,
            observation_id,
            accepted=self.accepted,
            method=self.method,
            method_version=self.method_version,
            rationale=self.rationale,
            provenance=self.provenance,
            assessed_at=created_at,
        )


@dataclass(frozen=True, slots=True)
class ExplorationAdmissionRuntime:
    """Host-owned policy for admitting previously accepted observations."""

    allowed_input_ids: tuple[str, ...]

    def admit(self, store: Any, observation_id: str, *, created_at: str) -> Any:
        observation = store.get_exploration_observation(observation_id)
        if observation is None:
            raise PlannerActionError("exploration observation does not exist")
        if not set(observation.input_ids).issubset(self.allowed_input_ids):
            raise PlannerActionError("observation inputs are outside the host-owned admission scope")
        assessments = [
            item
            for item in store.iter_exploration_observation_assessments(observation_id)
            if item.accepted
        ]
        if not assessments:
            raise PlannerActionError("observation has no accepted assessment")
        assessment = assessments[-1]
        return admit_exploration_observation(store, observation_id, assessment.id, created_at)


class PlannerActionError(ValueError):
    """The planner proposed an action that violates the bounded action contract."""


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
    execution_spec: Mapping[str, Any] | None = None
    evidence_capability: str | None = None
    evidence_parameters: Mapping[str, Any] | None = None
    requested_representation: str | None = None
    rationale: str = ""

    def __post_init__(self) -> None:
        if self.kind not in {"scout", "assess_exploration", "admit_exploration", "discover_gap", "question", "hypothesis", "prediction", "experiment", "request_evidence", "stop"}:
            raise PlannerActionError(f"unknown discovery action: {self.kind}")
        if not self.rationale.strip():
            raise PlannerActionError("discovery action requires a rationale")
        if self.kind == "request_evidence":
            _require(self.evidence_capability, "evidence_capability")
            if self.evidence_parameters is None or not isinstance(self.evidence_parameters, Mapping):
                raise PlannerActionError("request_evidence requires evidence_parameters")
            _require(self.requested_representation, "requested_representation")


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
    exploration_observations: tuple[Mapping[str, Any], ...] = ()
    exploration_assessments: tuple[Mapping[str, Any], ...] = ()


class Planner(Protocol):
    def choose(self, context: DiscoveryContext) -> DiscoveryAction:
        """Choose exactly one bounded next action from the supplied context."""


class ExplorationAssessmentRuntimeProtocol(Protocol):
    def assess(self, store: Any, observation_id: str, *, created_at: str) -> Any:
        """Apply host-owned assessment policy."""


class ExplorationAdmissionRuntimeProtocol(Protocol):
    def admit(self, store: Any, observation_id: str, *, created_at: str) -> Any:
        """Apply host-owned admission policy."""


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


def _exploration_observation_view(item: Any) -> dict[str, Any]:
    return {"id": item.id, "observation": item.observation, "input_ids": tuple(item.input_ids), "evidence": tuple(item.evidence), "method": item.method, "method_version": item.method_version, "uncertainty": item.uncertainty, "parameters": dict(item.parameters) if item.parameters is not None else None}


def _exploration_assessment_view(item: Any) -> dict[str, Any]:
    return {"id": item.id, "observation_id": item.observation_id, "accepted": item.accepted, "method": item.method, "method_version": item.method_version, "rationale": item.rationale}


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
        "execution_spec": dict(item.execution_spec) if item.execution_spec is not None else None,
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
        exploration_observations=tuple(_exploration_observation_view(item) for item in store.iter_exploration_observations()),
        exploration_assessments=tuple(_exploration_assessment_view(item) for item in store.iter_exploration_observation_assessments()),
        hypotheses=tuple(_hypothesis_view(item) for item in store.iter_hypotheses()),
        predictions=tuple(_prediction_view(item) for item in store.iter_predictions()),
        experiments=tuple(_experiment_view(item) for item in store.iter_experiment_proposals()),
        evaluations=tuple(_evaluation_view(item) for item in store.iter_prediction_evaluations()),
        consequences=tuple(_consequence_view(item) for item in store.iter_knowledge_state_consequences()),
        actions_taken=actions_taken,
        feedback=feedback,
    )


def _require(value: str | None, field: str) -> str:
    if value is None:
        raise PlannerActionError(f"{field} is required for this discovery action")
    if not isinstance(value, str):
        raise PlannerActionError(f"{field} must be a string")
    if not value.strip():
        raise PlannerActionError(f"{field} is required for this discovery action")
    return value



def _validate_execution_spec(
    raw: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if raw is None:
        raise PlannerActionError("experiment action requires execution_spec")
    if not isinstance(raw, Mapping):
        raise PlannerActionError("execution_spec must be an object")
    try:
        spec = ExecutableExperimentSpec(**dict(raw))
    except (TypeError, ValueError) as exc:
        raise PlannerActionError(f"invalid execution_spec: {exc}") from exc
    return {
        "operation": spec.operation,
        "position": float(spec.position),
        "position_key": spec.position_key,
        "expected_presence": dict(spec.expected_presence),
    }


def _validate_action_state(
    store: Any,
    action: DiscoveryAction,
    *,
    enforce_exploration_policy: bool,
) -> None:
    """Enforce bounded discovery transitions at the host boundary.

    The planner remains free to choose the next action, but only actions that
    are legal for the represented state may be executed. Exploration policy
    is enforced when the caller has supplied the corresponding host-owned
    assessment/admission capabilities; legacy scout-only bindings remain
    valid for bounded exploration and structural-discovery tests.
    """
    observations = tuple(store.iter_exploration_observations())
    assessments = tuple(store.iter_exploration_observation_assessments())
    findings = tuple(store.iter_discovery_findings())
    hypotheses = tuple(store.iter_hypotheses())
    predictions = tuple(store.iter_predictions())
    experiments = tuple(store.iter_experiment_proposals())

    if action.kind == "scout":
        if observations:
            raise PlannerActionError("scout is unavailable after an exploration observation exists")
        return

    if action.kind == "assess_exploration":
        if not enforce_exploration_policy:
            raise PlannerActionError("exploration assessment is unavailable without host-owned assessment policy")
        if not observations:
            raise PlannerActionError("assess_exploration requires an exploration observation")
        if any(
            not any(item.observation_id == observation.id for item in assessments)
            for observation in observations
        ):
            return
        raise PlannerActionError("all exploration observations have already been assessed")

    if action.kind == "admit_exploration":
        if not enforce_exploration_policy:
            raise PlannerActionError("exploration admission is unavailable without host-owned admission policy")
        if any(
            assessment.accepted
            and not any(
                finding.kind is DiscoveryFindingKind.EXPLORATION_OBSERVATION
                and assessment.observation_id in finding.context_ids
                for finding in findings
            )
            for assessment in assessments
        ):
            return
        raise PlannerActionError("no accepted exploration observation is pending admission")

    if enforce_exploration_policy and observations:
        unassessed = any(
            not any(item.observation_id == observation.id for item in assessments)
            for observation in observations
        )
        if unassessed:
            raise PlannerActionError(
                "exploration observation must be assessed before another action"
            )
        accepted_pending = any(
            assessment.accepted
            and not any(
                finding.kind is DiscoveryFindingKind.EXPLORATION_OBSERVATION
                and assessment.observation_id in finding.context_ids
                for finding in findings
            )
            for assessment in assessments
        )
        if accepted_pending:
            raise PlannerActionError(
                "accepted exploration observation must be admitted before another action"
            )

    candidate_findings = tuple(
        finding
        for finding in findings
        if finding.kind in {DiscoveryFindingKind.GAP, DiscoveryFindingKind.TENSION}
    )

    if experiments:
        evaluations = tuple(store.iter_prediction_evaluations())
        if not evaluations:
            raise PlannerActionError("the bounded investigation requires experiment evaluation before another action")
        if action.kind not in {"stop", "request_evidence"}:
            raise PlannerActionError(
                "the bounded investigation permits stop or a bounded evidence request after experiment evaluation"
            )
        return

    if action.kind == "stop":
        # Stopping before a GAP is a valid bounded exploration termination.
        # Once a candidate gap/tension exists, termination requires the
        # bounded experiment and its deterministic evaluation.
        if candidate_findings:
            raise PlannerActionError("stop is unavailable before a bounded experiment")
        return

    if not candidate_findings:
        if action.kind != "discover_gap":
            raise PlannerActionError(
                "bounded discovery requires a GAP or TENSION finding before candidate generation"
            )
        return

    hypothesis_counts = {
        finding.id: sum(finding.id in item.finding_ids for item in hypotheses)
        for finding in candidate_findings
    }
    pending_hypothesis = next(
        (finding for finding in candidate_findings if hypothesis_counts[finding.id] < 2),
        None,
    )

    if pending_hypothesis is not None:
        count = hypothesis_counts[pending_hypothesis.id]
        if count == 0:
            if action.kind not in {"hypothesis", "question"}:
                raise PlannerActionError(
                    "a GAP or TENSION requires an initial hypothesis before predictions"
                )
        elif count == 1:
            if action.kind != "hypothesis":
                raise PlannerActionError(
                    "a single hypothesis requires a competing hypothesis before prediction"
                )
        return

    if not predictions:
        if action.kind != "prediction":
            raise PlannerActionError(
                "competing hypotheses require discriminating predictions before experiment"
            )
        return

    if action.kind != "experiment":
        raise PlannerActionError(
            "existing predictions require a bounded experiment before another action"
        )

def execute_action(store: Any, action: DiscoveryAction, *, created_at: str) -> tuple[str, ...]:
    """Validate and execute one action using existing Episteme primitives."""
    if action.kind == "stop":
        return ()

    if action.kind == "scout":
        raise PlannerActionError("scout action requires the host-owned exploration runtime")

    if action.kind == "discover_gap":
        raise PlannerActionError("discover_gap action requires the host-owned structural discovery runtime")

    if action.kind == "request_evidence":
        raise PlannerActionError("request_evidence action requires the host-owned evidence request runtime")

    if not action.target_ids:
        raise PlannerActionError(f"{action.kind} action requires target_ids")

    if action.kind == "question":
        if len(action.target_ids) != 1:
            raise PlannerActionError("question action requires exactly one finding")
        finding = store.get_discovery_finding(action.target_ids[0])
        if finding is None:
            raise PlannerActionError("question target finding does not exist")
        if finding.kind not in {DiscoveryFindingKind.GAP, DiscoveryFindingKind.TENSION}:
            raise PlannerActionError("question target must be a gap or tension finding")
        question = question_from_finding(finding, created_at)
        store.put_discovery_finding(question)
        return (question.id,)

    if action.kind == "hypothesis":
        if len(action.target_ids) != 1:
            raise PlannerActionError("hypothesis action requires exactly one finding")
        statement = _require(action.statement, "statement")
        finding = store.get_discovery_finding(action.target_ids[0])
        if finding is None:
            raise PlannerActionError("hypothesis target finding does not exist")
        if finding.kind is DiscoveryFindingKind.GAP:
            from .proposals import complete_structural_gap

            try:
                hypothesis = complete_structural_gap(
                    store,
                    gap_id=finding.id,
                    statement=statement,
                    method="planner-driven-structural-gap-completion",
                    method_version="1",
                    rationale=action.rationale,
                    created_at=created_at,
                )
            except ValueError as exc:
                raise PlannerActionError(str(exc)) from exc
        else:
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
            raise PlannerActionError("prediction action requires at least two hypothesis ids")
        conditions = _require(action.conditions, "conditions")
        consequences = action.consequences
        if not consequences:
            consequence = _require(action.consequence, "consequence")
            consequences = tuple(consequence for _ in action.target_ids)
        if len(consequences) != len(action.target_ids):
            raise PlannerActionError("prediction consequences must match hypothesis targets")
        predictions = []
        try:
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
                predictions.append(prediction)
        except ValueError as exc:
            raise PlannerActionError(str(exc)) from exc

        for prediction in predictions:
            store.put_prediction(prediction)
        return tuple(prediction.id for prediction in predictions)

    if action.kind == "experiment":
        if len(action.target_ids) < 2:
            raise PlannerActionError("experiment action requires at least two prediction ids")
        execution_spec = _validate_execution_spec(action.execution_spec)
        if set(execution_spec["expected_presence"]) != set(action.target_ids):
            raise PlannerActionError(
                "execution_spec expected_presence must exactly match experiment prediction ids"
            )
        try:
                proposal = propose_candidate_discrimination_experiment(
            store,
            prediction_ids=action.target_ids,
            objective=_require(action.objective, "objective"),
            proposed_observation=_require(action.proposed_observation, "proposed_observation"),
            discrimination_basis=_require(action.discrimination_basis, "discrimination_basis"),
            conditions=_require(action.conditions, "conditions"),
            execution_spec=_validate_execution_spec(action.execution_spec),
            method="planner-driven-experiment",
            method_version="1",
            rationale=action.rationale,
            created_at=created_at,
        )
        except ValueError as exc:
            raise PlannerActionError(str(exc)) from exc
        store.put_experiment_proposal(proposal)
        return (proposal.id,)

    raise PlannerActionError(f"unsupported discovery action: {action.kind}")


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
    exploration_runtime: ExplorationRuntime | None = None,
    structural_discovery_runtime: StructuralDiscoveryRuntime | None = None,
    exploration_assessment_runtime: ExplorationAssessmentRuntimeProtocol | None = None,
    exploration_admission_runtime: ExplorationAdmissionRuntimeProtocol | None = None,
    evidence_request_runtime: EvidenceRequestRuntime | None = None,
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
                if not isinstance(action, DiscoveryAction):
                    raise PlannerActionError("planner must return DiscoveryAction")
                _validate_action_state(
                    store,
                    action,
                    enforce_exploration_policy=(
                        exploration_assessment_runtime is not None
                        or exploration_admission_runtime is not None
                    ),
                )
                if action.kind == "stop":
                    return DiscoveryRun(
                        status="stopped",
                        steps=tuple(steps),
                        stop_reason=action.rationale,
                    )
                if action.kind == "scout":
                    if exploration_runtime is None:
                        raise PlannerActionError("scout action is unavailable without a host-owned exploration runtime")
                    observation = exploration_runtime.scout(store, created_at=started_at)
                    output_ids = (observation.id,)
                elif action.kind == "discover_gap":
                    if structural_discovery_runtime is None:
                        raise PlannerActionError("structural discovery is unavailable without a host-owned structural discovery runtime")
                    pending_admission = any(
                        item.accepted
                        and not any(
                            finding.kind is DiscoveryFindingKind.EXPLORATION_OBSERVATION
                            and item.observation_id in finding.context_ids
                            for finding in store.iter_discovery_findings()
                        )
                        for item in store.iter_exploration_observation_assessments()
                    )
                    if pending_admission:
                        raise PlannerActionError(
                            "accepted exploration observation must be admitted before structural discovery"
                        )
                    finding = structural_discovery_runtime.discover(store, created_at=started_at)
                    output_ids = (finding.id,)
                elif action.kind == "assess_exploration":
                    if exploration_assessment_runtime is None:
                        raise PlannerActionError("exploration assessment is unavailable without a host-owned assessment runtime")
                    if len(action.target_ids) != 1:
                        raise PlannerActionError("assess_exploration action requires exactly one observation id")
                    assessment = exploration_assessment_runtime.assess(store, action.target_ids[0], created_at=started_at)
                    output_ids = (assessment.id,)
                elif action.kind == "admit_exploration":
                    if exploration_admission_runtime is None:
                        raise PlannerActionError("exploration admission is unavailable without a host-owned admission runtime")
                    if len(action.target_ids) != 1:
                        raise PlannerActionError("admit_exploration action requires exactly one observation id")
                    finding = exploration_admission_runtime.admit(store, action.target_ids[0], created_at=started_at)
                    output_ids = (finding.id,)
                elif action.kind == "request_evidence":
                    if evidence_request_runtime is None:
                        raise PlannerActionError("evidence request is unavailable without a host-owned evidence request runtime")
                    if not action.target_ids:
                        raise PlannerActionError("request_evidence action requires at least one motivation id")
                    request = EvidenceRequest(
                        capability=_require(action.evidence_capability, "evidence_capability"),
                        parameters=action.evidence_parameters or {},
                        rationale=action.rationale,
                        motivation_ids=action.target_ids,
                        requested_representation=_require(action.requested_representation, "requested_representation"),
                    )
                    result = evidence_request_runtime.request_evidence(
                        store, request, created_at=started_at
                    )
                    output_ids = (result.id,)
                else:
                    output_ids = execute_action(store, action, created_at=started_at)
            except PlannerActionError as exc:
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

            feedback.clear()
            if action.kind == "experiment":
                proposal = store.get_experiment_proposal(output_ids[0])
                if proposal is None:
                    raise RuntimeError("experiment action did not persist its proposal")
                active_runtime = experiment_runtime
                if active_runtime is None:
                    if proposal.execution_spec is None:
                        raise RuntimeError("experiment proposal has no executable specification")
                    spec = ExecutableExperimentSpec(**dict(proposal.execution_spec))
                    executor, evaluator_factory = build_registered_experiment_runtime(spec)
                    active_runtime = ExperimentRuntime(
                        executor=executor,
                        evaluator_factory=evaluator_factory,
                        comparison_conditions=proposal.conditions,
                    )
                output_ids = _execute_experiment_cycle(
                    store,
                    proposal,
                    grounded_input_ids=grounded_input_ids,
                    runtime=active_runtime,
                    created_at=started_at,
                )
            steps.append(DiscoveryStep(action=action, output_ids=output_ids))
            actions.append(action)
            break

    return DiscoveryRun(
        status="budget_exhausted",
        steps=tuple(steps),
        stop_reason=f"maximum discovery step budget reached: {max_steps}",
    )