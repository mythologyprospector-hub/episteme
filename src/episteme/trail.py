"""Reproducible reconstruction of discovery lineage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .model import canonical_json
from .store import Store

TRAIL_METHOD = "closed-loop-lineage"
TRAIL_METHOD_VERSION = "1"
TRAIL_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class TrailEntry:
    """One deterministic object and the explicit reference that reached it."""

    kind: str
    id: str
    via: str
    data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "id": self.id, "via": self.via, "data": self.data}


@dataclass(frozen=True, slots=True)
class DiscoveryTrail:
    """Read-only, reproducible reconstruction of a discovery lineage."""

    finding_id: str
    entries: tuple[TrailEntry, ...]
    method: str
    method_version: str
    created_at: str
    schema_version: int = TRAIL_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "entries": [entry.to_dict() for entry in self.entries],
            "method": self.method,
            "method_version": self.method_version,
            "created_at": self.created_at,
            "schema_version": self.schema_version,
        }

    def to_json(self) -> str:
        return canonical_json(self.to_dict())


def build_discovery_trail(
    store: Store,
    finding_id: str,
    created_at: str,
) -> DiscoveryTrail:
    """Reconstruct explicit upstream lineage without inference."""

    finding = store.get_discovery_finding(finding_id)
    if finding is None:
        raise ValueError(f"discovery trail references missing finding: {finding_id}")

    entries: list[TrailEntry] = []
    seen: set[tuple[str, str]] = set()

    def add(kind: str, identifier: str, via: str, data: dict[str, Any]) -> bool:
        key = (kind, identifier)
        if key in seen:
            return False
        seen.add(key)
        entries.append(TrailEntry(kind, identifier, via, data))
        return True

    def grounded(identifier: str, via: str) -> None:
        record = store.get_record(identifier)
        if record is not None:
            add("record", record.id, via, record.to_dict())
            return
        relationship = store.get_relationship(identifier)
        if relationship is not None:
            add("relationship", relationship.id, via, relationship.to_dict())
            return
        raise ValueError(f"discovery trail references missing grounded input: {identifier}")

    def finding_node(node, via: str) -> None:
        if not add("discovery_finding", node.id, via, node.to_dict()):
            return
        for context_id in node.context_ids:
            evaluation = store.get_prediction_evaluation(context_id)
            if evaluation is not None:
                evaluation_node(evaluation, f"{node.id}.context_ids")
                continue
            consequence = store.get_knowledge_state_consequence(context_id)
            if consequence is not None:
                consequence_node(consequence, f"{node.id}.context_ids")
                continue
            raise ValueError(f"discovery trail references missing generated context: {context_id}")
        for input_id in node.input_ids:
            grounded(input_id, f"{node.id}.input_ids")
        if node.related_finding_id is not None:
            parent = store.get_discovery_finding(node.related_finding_id)
            if parent is None:
                raise ValueError(
                    f"discovery trail references missing related finding: {node.related_finding_id}"
                )
            finding_node(parent, f"{node.id}.related_finding_id")

    def evaluation_node(node, via: str) -> None:
        if not add("prediction_evaluation", node.id, via, node.to_dict()):
            return
        result = store.get_record(node.result_id)
        if result is None or result.kind.value != "result":
            raise ValueError(f"discovery trail references missing grounded result: {node.result_id}")
        add("record", result.id, f"{node.id}.result_id", result.to_dict())
        prediction = store.get_prediction(node.prediction_id)
        if prediction is None:
            raise ValueError(f"discovery trail references missing prediction: {node.prediction_id}")
        prediction_node(prediction, f"{node.id}.prediction_id")
        if node.experiment_proposal_id is not None:
            proposal = store.get_experiment_proposal(node.experiment_proposal_id)
            if proposal is None:
                raise ValueError(
                    "discovery trail references missing experiment proposal: "
                    + node.experiment_proposal_id
                )
            proposal_node(proposal, f"{node.id}.experiment_proposal_id")

    def consequence_node(node, via: str) -> None:
        if not add("knowledge_state_consequence", node.id, via, node.to_dict()):
            return
        for evaluation_id in node.evaluation_ids:
            evaluation = store.get_prediction_evaluation(evaluation_id)
            if evaluation is None:
                raise ValueError(
                    f"discovery trail references missing prediction evaluation: {evaluation_id}"
                )
            evaluation_node(evaluation, f"{node.id}.evaluation_ids")
        if node.target_kind.value == "hypothesis":
            target = store.get_hypothesis(node.target_id)
            if target is None:
                raise ValueError(f"discovery trail references missing hypothesis: {node.target_id}")
            hypothesis_node(target, f"{node.id}.target_id")
        elif node.target_kind.value == "model":
            target = store.get_model(node.target_id)
            if target is None:
                raise ValueError(f"discovery trail references missing model: {node.target_id}")
            model_node(target, f"{node.id}.target_id")
        else:
            target = store.get_prediction(node.target_id)
            if target is None:
                raise ValueError(f"discovery trail references missing prediction: {node.target_id}")
            prediction_node(target, f"{node.id}.target_id")

    def prediction_node(node, via: str) -> None:
        if not add("prediction", node.id, via, node.to_dict()):
            return
        target = store.get_hypothesis(node.source_id)
        if target is not None:
            hypothesis_node(target, f"{node.id}.source_id")
            return
        target = store.get_model(node.source_id)
        if target is not None:
            model_node(target, f"{node.id}.source_id")
            return
        raise ValueError(f"discovery trail references missing prediction source: {node.source_id}")

    def proposal_node(node, via: str) -> None:
        if not add("experiment_proposal", node.id, via, node.to_dict()):
            return
        for prediction_id in node.prediction_ids:
            prediction = store.get_prediction(prediction_id)
            if prediction is None:
                raise ValueError(
                    f"discovery trail references missing proposal prediction: {prediction_id}"
                )
            prediction_node(prediction, f"{node.id}.prediction_ids")

    def hypothesis_node(node, via: str) -> None:
        if not add("hypothesis", node.id, via, node.to_dict()):
            return
        for finding_id in node.finding_ids:
            parent = store.get_discovery_finding(finding_id)
            if parent is None:
                raise ValueError(
                    f"discovery trail references missing motivating finding: {finding_id}"
                )
            finding_node(parent, f"{node.id}.finding_ids")
        for input_id in node.input_ids:
            grounded(input_id, f"{node.id}.input_ids")

    def model_node(node, via: str) -> None:
        if not add("model", node.id, via, node.to_dict()):
            return
        for hypothesis_id in node.hypothesis_ids:
            target = store.get_hypothesis(hypothesis_id)
            if target is None:
                raise ValueError(
                    f"discovery trail references missing model hypothesis: {hypothesis_id}"
                )
            hypothesis_node(target, f"{node.id}.hypothesis_ids")
        for input_id in node.input_ids:
            grounded(input_id, f"{node.id}.input_ids")

    finding_node(finding, "trail.root")
    return DiscoveryTrail(
        finding_id=finding.id,
        entries=tuple(entries),
        method=TRAIL_METHOD,
        method_version=TRAIL_METHOD_VERSION,
        created_at=created_at,
    )
