"""Bounded planner-driven discovery control.

The planner chooses among a small, explicit action vocabulary. It never receives
direct access to the Store and cannot execute arbitrary code. This module is
control-plane machinery, not an epistemic authority.
"""

from __future__ import annotations

import re

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Protocol

from .discovery import detect_positional_gap, question_from_finding
from .capture import CaptureOutcome
from .evidence_request import EvidenceRequest, EvidenceRequestRejected
from .exploration import scout_positional_records
from .exploration_bridge import admit_exploration_observation, assess_exploration_observation
from .model import Provenance, canonical_json
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
    expected_presences: Mapping[str, bool] | None = None
    predicted_numeric_value: float | None = None
    predicted_numeric_values: Mapping[str, float] | None = None
    quantitative_rule: Mapping[str, Any] | None = None
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
        if self.predicted_numeric_values is not None:
            if not isinstance(self.predicted_numeric_values, Mapping):
                raise PlannerActionError("predicted_numeric_values must be an object")
            import math
            if any(
                isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                for value in self.predicted_numeric_values.values()
            ):
                raise PlannerActionError("predicted_numeric_values values must be finite numbers")
            if len(self.predicted_numeric_values) > 1 and len(set(self.predicted_numeric_values.values())) != len(self.predicted_numeric_values):
                raise PlannerActionError("competing numeric predictions must have distinct predicted values")
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
    grounded_observations: tuple[Mapping[str, Any], ...] = ()
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


def _grounded_observation_view(record: Any) -> dict[str, Any]:
    return {
        "id": record.id,
        "kind": record.kind.value,
        "payload": dict(record.payload),
        "created_at": record.created_at,
    }


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
        "quantitative_rule": dict(item.quantitative_rule) if item.quantitative_rule is not None else None,
    }


def _prediction_view(item: Any) -> dict[str, Any]:
    return {
        "id": item.id,
        "source_id": item.source_id,
        "consequence": item.consequence,
        "conditions": item.conditions,
        "comparison_hypothesis_ids": tuple(item.comparison_hypothesis_ids),
        "predicted_numeric_value": item.predicted_numeric_value,
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
    grounded_records = tuple(
        record
        for record_id in grounded_input_ids
        if (record := store.get_record(record_id)) is not None
    )
    return DiscoveryContext(
        grounded_input_ids=tuple(grounded_input_ids),
        grounded_observations=tuple(_grounded_observation_view(record) for record in grounded_records),
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
    result = {"operation": spec.operation}
    if spec.position is not None:
        result["position"] = float(spec.position)
    if spec.operation == "positional_presence":
        result["position_key"] = spec.position_key
    return result



def _record_content_provenance_key(record: Any) -> tuple[str, tuple[str, ...]]:
    """Return the identity-independent grounded content/provenance fingerprint."""
    return (
        canonical_json(dict(record.payload)),
        tuple(canonical_json(item.to_dict()) for item in record.provenance),
    )


def _validate_experiment_input_independence(
    store: Any,
    grounded_input_ids: tuple[str, ...],
    experiment_input_ids: tuple[str, ...],
) -> None:
    """Reject held-out inputs that duplicate grounded records under new IDs."""
    grounded_records = [store.get_record(record_id) for record_id in grounded_input_ids]
    experiment_records = [store.get_record(record_id) for record_id in experiment_input_ids]
    if any(record is None for record in grounded_records):
        raise RuntimeError("bounded experiment grounding contains an unknown record")
    if any(record is None for record in experiment_records):
        raise RuntimeError("bounded experiment input scope contains an unknown record")
    grounded_keys = {_record_content_provenance_key(record) for record in grounded_records}
    duplicated = [
        record.id for record in experiment_records
        if _record_content_provenance_key(record) in grounded_keys
    ]
    if duplicated:
        raise RuntimeError(
            "bounded experiment input scope contains a content/provenance duplicate "
            "of a discovery input"
        )


def _validate_positional_prediction_bindings(store: Any, action: DiscoveryAction) -> None:
    """Reject positional predictions whose expectation contradicts their hypothesis."""
    if not action.execution_spec or action.execution_spec.get("operation") != "positional_presence":
        return
    predictions = {item.id: item for item in store.iter_predictions()}
    hypotheses = {item.id: item for item in store.iter_hypotheses()}
    position = float(action.execution_spec["position"])
    pattern = re.compile(r"\b(not\s+)?at\s+position\s+([-+]?(?:\d+(?:\.\d*)?|\.\d+))\b", re.IGNORECASE)
    for prediction_id in action.target_ids:
        prediction = predictions.get(prediction_id)
        if prediction is None:
            continue
        hypothesis = hypotheses.get(prediction.source_id)
        if hypothesis is None or prediction.expected_presence is None:
            continue
        match = pattern.search(hypothesis.statement)
        if match is None:
            continue
        claimed_position = float(match.group(2))
        if claimed_position != position:
            raise PlannerActionError(
                "positional prediction target does not match its hypothesis position"
            )
        expected = match.group(1) is None
        if prediction.expected_presence is not expected:
            raise PlannerActionError(
                "positional prediction expected_presence contradicts its source hypothesis"
            )

def _validate_action_state(
    store: Any,
    action: DiscoveryAction,
    *,
    enforce_exploration_policy: bool,
    actions_taken: tuple[DiscoveryAction, ...] = (),
    evidence_request_completed: bool = False,
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

    if action.kind == "stop":
        # A successful request_evidence action enters actions_taken only
        # after its host-owned runtime returns successfully. Treat that immediately
        # preceding completed action as the terminal transition marker.
        if evidence_request_completed:
            return
        if actions_taken and actions_taken[-1].kind == "request_evidence":
            return
        # A completed and evaluated bounded experiment is also a legal terminal
        # transition. The planner's stop remains blocked before that boundary.
        if experiments and tuple(store.iter_prediction_evaluations()):
            return
        # Stopping before a GAP is a valid bounded exploration termination.
        # Once a candidate gap/tension exists, termination requires the
        # bounded experiment and its deterministic evaluation.
        if candidate_findings:
            raise PlannerActionError("stop is unavailable before a bounded experiment")
        if enforce_exploration_policy and observations and any(
            finding.kind is DiscoveryFindingKind.EXPLORATION_OBSERVATION
            and any(observation.id in finding.context_ids for observation in observations)
            for finding in findings
        ):
            raise PlannerActionError(
                "structural gap discovery is required after accepted exploration"
            )
        return

    if experiments:
        evaluations = tuple(store.iter_prediction_evaluations())
        if not evaluations:
            raise PlannerActionError("the bounded investigation requires experiment evaluation before another action")
        if action.kind != "request_evidence":
            raise PlannerActionError(
                "the bounded investigation permits a bounded evidence request after experiment evaluation"
            )
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
    _validate_positional_prediction_bindings(store, action)

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
                    quantitative_rule=dict(action.quantitative_rule) if action.quantitative_rule is not None else None,
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
                quantitative_rule=dict(action.quantitative_rule) if action.quantitative_rule is not None else None,
                created_at=created_at,
            )
        existing = tuple(
            item
            for item in store.iter_hypotheses()
            if set(item.finding_ids) == set(hypothesis.finding_ids)
        )
        normalized = " ".join(hypothesis.statement.lower().split())
        if any(" ".join(item.statement.lower().split()) == normalized for item in existing):
            raise PlannerActionError(
                "competing hypotheses must be distinct; duplicate hypothesis statement rejected"
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
        if action.predicted_numeric_values is not None:
            if set(action.predicted_numeric_values) != set(action.target_ids):
                raise PlannerActionError("predicted_numeric_values must exactly match hypothesis targets")
            if action.expected_presences is not None:
                raise PlannerActionError("numeric predictions must not include expected_presences")
            numeric_values = {
                candidate_id: float(action.predicted_numeric_values[candidate_id])
                for candidate_id in action.target_ids
            }
            if len(set(numeric_values.values())) != len(numeric_values):
                raise PlannerActionError(
                    "competing numeric predictions must have distinct predicted values"
                )
            expected_presences = {}
        else:
            if not isinstance(action.expected_presences, Mapping) or set(action.expected_presences) != set(action.target_ids):
                raise PlannerActionError("prediction expected_presences must exactly match hypothesis targets")
            if any(not isinstance(value, bool) for value in action.expected_presences.values()):
                raise PlannerActionError("prediction expected_presences values must be booleans")
            numeric_values = {
                candidate_id: action.predicted_numeric_value
                for candidate_id in action.target_ids
            }
            expected_presences = action.expected_presences
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
                    expected_presence=expected_presences.get(candidate_id),
                    predicted_numeric_value=numeric_values[candidate_id],
                    created_at=created_at,
                )
                predictions.append(prediction)
        except ValueError as exc:
            raise PlannerActionError(str(exc)) from exc

        for prediction in predictions:
            store.put_prediction(prediction)
        return tuple(prediction.id for prediction in predictions)

    if action.kind == "experiment":
        _validate_positional_prediction_bindings(store, action)
        if len(action.target_ids) < 2:
            raise PlannerActionError("experiment action requires at least two prediction ids")
        execution_spec = _validate_execution_spec(action.execution_spec)
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



def _host_experiment_assessment(evaluations: tuple[Any, ...]) -> str:
    """Summarize deterministic prediction evaluations without treating them as truth."""
    outcomes = [
        getattr(getattr(item, "outcome", None), "value", getattr(item, "outcome", None))
        for item in evaluations
    ]
    consistent = outcomes.count("consistent")
    inconsistent = outcomes.count("inconsistent")
    unresolved = len(outcomes) - consistent - inconsistent

    if not outcomes:
        return "Host assessment: no prediction evaluations are available."
    if consistent == len(outcomes):
        finding = "all evaluated predictions are consistent with the experiment"
    elif inconsistent == len(outcomes):
        finding = "all evaluated predictions are contradicted by the experiment"
    elif consistent and inconsistent:
        finding = "evaluation outcomes are mixed: some predictions are consistent and others are contradicted"
    else:
        finding = "the evaluation does not resolve the predictions"

    details = (
        f"{consistent} consistent, {inconsistent} inconsistent, "
        f"{unresolved} unresolved out of {len(outcomes)} evaluation(s)"
    )
    return (
        f"Host-derived experiment assessment: {finding} ({details}). "
        "Consistency is not proof of truth, and the planner's rationale is not evaluation evidence."
    )


def _evaluations_produced_by_run(store: Any, steps: list[DiscoveryStep]) -> tuple[Any, ...]:
    """Return only evaluations whose IDs were emitted by this discovery run."""
    run_output_ids = {
        output_id
        for step in steps
        for output_id in step.output_ids
    }
    if not run_output_ids:
        return ()
    return tuple(
        evaluation
        for evaluation in store.iter_prediction_evaluations()
        if evaluation.id in run_output_ids
    )


def run_autonomous_discovery(
    store: Any,
    planner: Planner,
    *,
    grounded_input_ids: tuple[str, ...],
    started_at: str,
    experiment_input_ids: tuple[str, ...] | None = None,
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
    evidence_request_completed = False

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
                    actions_taken=tuple(actions),
                    evidence_request_completed=evidence_request_completed,
                )
                if action.kind == "stop":
                    stop_reason = action.rationale
                    evaluations = _evaluations_produced_by_run(store, steps)
                    if evaluations:
                        stop_reason = (
                            f"{_host_experiment_assessment(evaluations)} "
                            f"Planner-authored stop rationale (unverified): {action.rationale}"
                        )
                    return DiscoveryRun(
                        status="stopped",
                        steps=tuple(steps),
                        stop_reason=stop_reason,
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
                    try:
                        request = EvidenceRequest(
                            capability=_require(action.evidence_capability, "evidence_capability"),
                            parameters=action.evidence_parameters or {},
                            rationale=action.rationale,
                            motivation_ids=action.target_ids,
                            requested_representation=_require(action.requested_representation, "requested_representation"),
                        )
                    except ValueError as exc:
                        raise PlannerActionError(
                            f"invalid evidence request: {exc}"
                        ) from exc
                    try:
                        result = evidence_request_runtime.request_evidence(
                            store, request, created_at=started_at
                        )
                    except EvidenceRequestRejected as exc:
                        return DiscoveryRun(
                            status="failed",
                            steps=tuple(steps),
                            stop_reason=f"bounded evidence request was rejected by host policy: {exc}",
                        )
                    except ValueError as exc:
                        raise PlannerActionError(
                            f"evidence request execution failed validation: {exc}"
                        ) from exc
                    if not hasattr(result, "outcome") or not hasattr(result, "id"):
                        raise RuntimeError(
                            "host evidence runtime returned an invalid capture result"
                        )
                    if not isinstance(result.outcome, CaptureOutcome):
                        raise RuntimeError(
                            "host evidence runtime returned an invalid capture outcome"
                        )
                    output_ids = (result.id,)
                    steps.append(DiscoveryStep(action=action, output_ids=output_ids))
                    actions.append(action)
                    if result.outcome.value == "complete":
                        evidence_request_completed = True
                        return DiscoveryRun(
                            status="stopped",
                            steps=tuple(steps),
                            stop_reason="bounded evidence request completed through the host-owned runtime",
                        )
                    outcome = result.outcome.value
                    if outcome == "partial":
                        return DiscoveryRun(
                            status="failed",
                            steps=tuple(steps),
                            stop_reason=(
                                "bounded evidence request returned a partial capture; "
                                "no complete evidence was established"
                            ),
                        )
                    if outcome == "failed":
                        return DiscoveryRun(
                            status="failed",
                            steps=tuple(steps),
                            stop_reason=(
                                "bounded evidence request failed through the host-owned runtime; "
                                "no evidence success was established"
                            ),
                        )
                    raise RuntimeError(
                        "host evidence runtime returned an unsupported capture outcome"
                    )
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
                if experiment_input_ids is None:
                    raise RuntimeError(
                        "bounded experiment requires an explicit host-owned input scope"
                    )
                if not experiment_input_ids:
                    raise RuntimeError("bounded experiment input scope must not be empty")
                overlap = set(grounded_input_ids) & set(experiment_input_ids)
                if overlap:
                    raise RuntimeError(
                        "bounded experiment input scope must be disjoint from discovery inputs"
                    )
                _validate_experiment_input_independence(
                    store,
                    grounded_input_ids,
                    experiment_input_ids,
                )
                output_ids = _execute_experiment_cycle(
                    store,
                    proposal,
                    grounded_input_ids=experiment_input_ids,
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